from src.core.ping_endpoint.service import PingEndpointService

def test_pingendpointservice_service():
    service = PingEndpointService()
    assert service.check() == "pong"
