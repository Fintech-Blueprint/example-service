from typing import Dict, Any
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from src.core.ping_endpoint.service import PingEndpointService

router = APIRouter()
service = PingEndpointService()  # Single instance

@router.get("/v1/ping")
def ping_endpoint() -> Dict[str, Any]:
    return service.check()

@router.get("/v1/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
