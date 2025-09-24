from fastapi import APIRouter, Depends, Header
from typing import Optional
import subprocess
import time
from prometheus_client import Gauge

router = APIRouter()

# Health metric as required by CTO
health_up = Gauge('health_up', 'Service health status (1=healthy, 0=unhealthy)')

@router.get("/healthz")
async def health_check(authorization: Optional[str] = Header(None)):
    """Health check endpoint with Prometheus metric."""
    try:
        # Get git commit for service version
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
        # Set health metric to 1 (healthy)
        health_up.set(1)
        return {
            "status": "healthy",
            "version": "1.0.0",
            "commit": commit,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metrics": {
                "health_up": 1
            }
        }
    except Exception as e:
        # Set health metric to 0 (unhealthy)
        health_up.set(0)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metrics": {
                "health_up": 0
            }
        }