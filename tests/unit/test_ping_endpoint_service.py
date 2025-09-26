from src.core.ping_endpoint.service import PingEndpointService
import pytest


@pytest.mark.unit
def test_pingendpointservice_service():
    service = PingEndpointService()
    assert service.check() == "pong"
