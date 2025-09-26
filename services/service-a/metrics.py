from prometheus_client import Counter, Histogram, Info
from typing import Callable
from fastapi import FastAPI, Response
import time

# Metrics definitions
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total count of HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=[.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

SERVICE_INFO = Info(
    'service_metadata',
    'Service version and compliance information'
)


def init_metrics(app: FastAPI) -> None:
    """Initialize metrics collection for the service"""

    SERVICE_INFO.info({
        'version': 'v1',
        'name': 'service-a',
        'phase': 'poc',
        'compliance_mode': 'sandbox'
    })

    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        start_time = time.time()

        response = await call_next(request)

        # Record request count and latency
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)

        return response
