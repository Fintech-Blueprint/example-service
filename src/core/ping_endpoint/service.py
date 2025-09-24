from datetime import datetime
import time
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge

# Service-specific metrics
PING_REQUESTS = Counter('ping_requests_total', 'Total number of ping requests')
PING_LATENCY = Histogram('ping_latency_seconds', 'Ping request latency in seconds')
LAST_SUCCESS = Gauge('ping_last_success_timestamp', 'Timestamp of last successful ping')
HEALTH_STATUS = Gauge('ping_health_status', 'Current health status (1=healthy, 0=unhealthy)')

class PingEndpointService:
    def __init__(self):
        self._start_time = datetime.utcnow()
        HEALTH_STATUS.set(1)  # Initialize as healthy

    def check(self) -> Dict[str, Any]:
        start = time.time()
        try:
            PING_REQUESTS.inc()
            uptime = (datetime.utcnow() - self._start_time).total_seconds()
            response = {
                "status": "healthy",
                "message": "pong",
                "uptime_seconds": uptime,
                "timestamp": datetime.utcnow().isoformat()
            }
            LAST_SUCCESS.set_to_current_time()
            return response
        finally:
            PING_LATENCY.observe(time.time() - start)
