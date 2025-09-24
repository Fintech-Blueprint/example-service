from fastapi import APIRouter, Depends, Header
from typing import Optional
import subprocess
import time
import os
from prometheus_client import Gauge, Counter

router = APIRouter()

# Health metrics as required by CTO
health_up = Gauge('health_up', 'Service health status (1=healthy, 0=unhealthy)')
retry_counter = Counter('healthcheck_retries_total', 'Total number of health check retries')
resource_usage = Gauge('resource_usage', 'Resource usage by type', ['resource_type'])

# Mode-specific configuration
SANDBOX_MODE = os.getenv('SERVICE_MODE', 'sandbox').lower() == 'sandbox'
CPU_LIMIT = 0.5 if SANDBOX_MODE else 16.0
MEMORY_LIMIT = 512 if SANDBOX_MODE else 32768

@router.get("/healthz")
async def health_check(authorization: Optional[str] = Header(None)):
    """Health check endpoint with Prometheus metrics and mode-specific behavior."""
    try:
        # Get git commit for service version
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
        
        # Get resource usage
        cpu_usage = float(subprocess.check_output(['ps', '-p', str(os.getpid()), '-o', '%cpu=']))
        memory_usage = float(subprocess.check_output(['ps', '-p', str(os.getpid()), '-o', 'rss=']).decode()) / 1024  # MB
        
        # Update resource metrics
        resource_usage.labels(resource_type='cpu').set(cpu_usage)
        resource_usage.labels(resource_type='memory').set(memory_usage)
        
        # Mode-specific resource validation
        resource_warning = None
        if not SANDBOX_MODE and (cpu_usage > CPU_LIMIT or memory_usage > MEMORY_LIMIT):
            health_up.set(0)
            return {
                "status": "unhealthy",
                "error": f"Resource limits exceeded: CPU={cpu_usage:.1f}, Memory={memory_usage:.1f}MB",
                "version": "1.0.0",
                "commit": commit,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "metrics": {
                    "health_up": 0,
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "mode": "compliance"
                }
            }
        elif SANDBOX_MODE and (cpu_usage > CPU_LIMIT or memory_usage > MEMORY_LIMIT):
            resource_warning = f"Resource usage high: CPU={cpu_usage:.1f}, Memory={memory_usage:.1f}MB"
        
        # Set health metric to 1 (healthy)
        health_up.set(1)
        
        response = {
            "status": "healthy",
            "version": "1.0.0",
            "commit": commit,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metrics": {
                "health_up": 1,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "mode": "sandbox" if SANDBOX_MODE else "compliance"
            }
        }
        
        if resource_warning:
            response["warnings"] = [resource_warning]
            
        return response
        
    except Exception as e:
        retry_counter.inc()  # Increment retry counter on failure
        health_up.set(0)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metrics": {
                "health_up": 0,
                "mode": "sandbox" if SANDBOX_MODE else "compliance"
            }
        }