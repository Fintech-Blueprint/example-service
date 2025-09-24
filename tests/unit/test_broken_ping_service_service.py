from src.core.broken_ping_service.service import BrokenPingServiceService

def test_brokenpingserviceservice_service():
    service = BrokenPingServiceService()
    assert service.check() == "pong"
