from prometheus_client import Counter, Gauge
import subprocess
from datetime import datetime

# Metrics as per CTO requirements
HEALTH_UP = Gauge('health_up', 'Service health status (1=healthy, 0=unhealthy)')
HEALTH_CHECK_COUNT = Counter('health_check_total', 'Total number of health checks')

def get_git_commit():
    """Get current git commit."""
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
    except:
        return "unknown"

def get_service_metrics():
    """Get service metrics."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "commit": get_git_commit(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }