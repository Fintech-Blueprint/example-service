from fastapi import APIRouter
from src.core.broken_ping_service.service import BrokenPingServiceService

router = APIRouter()

@router.get("/broken_ping_service")
def broken_ping_service():
    service = BrokenPingServiceService()
    return {"message": service.check()}
