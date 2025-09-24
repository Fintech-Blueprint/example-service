from fastapi import APIRouter, Depends, Header, Response
from typing import Optional, Dict
import subprocess
import time
import os
import yaml
from prometheus_client import Gauge, Counter, Histogram

router = APIRouter()

# Load org-level configuration
with open('org-config.yaml', 'r') as f:
    org_config = yaml.safe_load(f)

# Service identification
SERVICE_NAME = os.getenv('SERVICE_NAME', 'example-service')
SERVICE_MODE = os.getenv('SERVICE_MODE', 'sandbox').lower()

# Health and monitoring metrics
health_up = Gauge('health_up', 'Service health status (1=healthy, 0=unhealthy)', ['service'])
retry_counter = Counter('healthcheck_retries_total', 'Total number of health check retries', ['service'])
resource_usage = Gauge('resource_usage', 'Resource usage by type', ['service', 'resource_type'])
dependency_health = Gauge('dependency_health', 'Dependency health status', ['service', 'dependency'])
deployment_success = Counter('deployment_success', 'Deployment success counter', ['service', 'attempt'])
resource_usage_histogram = Histogram('resource_usage_histogram', 'Resource usage distribution', ['service', 'resource_type'])

# Mode-specific configuration
SANDBOX_MODE = SERVICE_MODE == 'sandbox'
CPU_LIMIT = org_config['org']['resource_limits'][SERVICE_MODE]['cpu'].split('-')[1]
MEMORY_LIMIT = int(org_config['org']['resource_limits'][SERVICE_MODE]['memory'].split('-')[1].replace('Mi', ''))

@router.get("/healthz")
async def health_check(authorization: Optional[str] = Header(None), response: Response = None):
    """Health check endpoint with multi-service monitoring and mode-specific behavior."""
    try:
        # Get git commit for service version
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
        
        # Get resource usage
        cpu_usage = float(subprocess.check_output(['ps', '-p', str(os.getpid()), '-o', '%cpu=']))
        memory_usage = float(subprocess.check_output(['ps', '-p', str(os.getpid()), '-o', 'rss=']).decode()) / 1024  # MB
        
        # Update resource metrics
        resource_usage.labels(service=SERVICE_NAME, resource_type='cpu').set(cpu_usage)
        resource_usage.labels(service=SERVICE_NAME, resource_type='memory').set(memory_usage)
        resource_usage_histogram.labels(service=SERVICE_NAME, resource_type='cpu').observe(cpu_usage)
        resource_usage_histogram.labels(service=SERVICE_NAME, resource_type='memory').observe(memory_usage)
        
        # Check dependencies (example)
        dependencies = {'database': True, 'cache': True}
        for dep, status in dependencies.items():
            dependency_health.labels(service=SERVICE_NAME, dependency=dep).set(1 if status else 0)
        
        # Mode-specific resource validation
        warnings = []
        if not SANDBOX_MODE and (cpu_usage > float(CPU_LIMIT) or memory_usage > float(MEMORY_LIMIT)):
            health_up.labels(service=SERVICE_NAME).set(0)
            retry_counter.labels(service=SERVICE_NAME).inc()
            
            if cpu_usage > float(CPU_LIMIT) * 0.9 or memory_usage > float(MEMORY_LIMIT) * 0.9:
                # Alert threshold reached
                response.status_code = 429  # Too Many Requests
                
            return {
                "status": "unhealthy",
                "error": f"Resource limits exceeded: CPU={cpu_usage:.1f}, Memory={memory_usage:.1f}MB",
                "version": "1.0.0",
                "commit": commit,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "service": SERVICE_NAME,
                "mode": SERVICE_MODE,
                "metrics": {
                    "health_up": 0,
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "dependencies": dependencies
                }
            }
        elif SANDBOX_MODE and (cpu_usage > float(CPU_LIMIT) or memory_usage > float(MEMORY_LIMIT)):
            warnings.append(f"Resource usage high: CPU={cpu_usage:.1f}, Memory={memory_usage:.1f}MB")
        
        # Service is healthy
        health_up.labels(service=SERVICE_NAME).set(1)
        deployment_success.labels(service=SERVICE_NAME, attempt='first').inc()
        
        response_data = {
            "status": "healthy",
            "version": "1.0.0",
            "commit": commit,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "service": SERVICE_NAME,
            "mode": SERVICE_MODE,
            "metrics": {
                "health_up": 1,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "dependencies": dependencies,
                "deployment_success": True,
                "retry_count": 0
            }
        }
        
        if warnings:
            response_data["warnings"] = warnings
            
        # Add monitoring headers for Golden Goose
        response.headers["X-Service-Health"] = "healthy"
        response.headers["X-Service-Mode"] = SERVICE_MODE
        response.headers["X-Resource-Usage"] = f"cpu={cpu_usage:.1f},memory={memory_usage:.1f}"
            
        return response_data
        
    except Exception as e:
        retry_counter.labels(service=SERVICE_NAME).inc()
        health_up.labels(service=SERVICE_NAME).set(0)
        
        error_response = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "service": SERVICE_NAME,
            "mode": SERVICE_MODE,
            "metrics": {
                "health_up": 0,
                "retry_count": retry_counter.labels(service=SERVICE_NAME)._value.get(),
                "dependencies": dependencies
            }
        }
        
        # Add monitoring headers for Golden Goose
        response.headers["X-Service-Health"] = "unhealthy"
        response.headers["X-Service-Mode"] = SERVICE_MODE
        response.headers["X-Error"] = str(e)
        
        return error_response