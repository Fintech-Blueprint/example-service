from fastapi import APIRouter
from src.core.ping_endpoint.service import PingEndpointService

router = APIRouter()


@router.get("/ping_endpoint")
def ping_endpoint():
    service = PingEndpointService()
    return {"message": service.check()}
