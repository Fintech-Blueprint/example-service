from datetime import datetime
import pytest
from prometheus_client import REGISTRY
from src.core.ping_endpoint.service import PingEndpointService

@pytest.fixture
def service():
    return PingEndpointService()

@pytest.mark.unit
def test_ping_response_structure(service):
    """Test that check returns correct response structure."""
    response = service.check()
    
    assert isinstance(response, dict)
    assert response["status"] == "healthy"
    assert response["message"] == "pong"
    assert isinstance(response["uptime_seconds"], float)
    assert "timestamp" in response
    
    # Validate ISO format timestamp
    datetime.fromisoformat(response["timestamp"])

@pytest.mark.unit
def test_prometheus_metrics(service):
    """Test that Prometheus metrics are updated."""
    # Get initial values
    initial_requests = REGISTRY.get_sample_value('ping_requests_total') or 0
    
    # Make a request
    service.check()
    
    # Verify metrics were updated
    assert REGISTRY.get_sample_value('ping_requests_total') == initial_requests + 1
    assert REGISTRY.get_sample_value('ping_health_status') == 1
    assert REGISTRY.get_sample_value('ping_last_success_timestamp') is not None
    assert REGISTRY.get_sample_value('ping_latency_seconds_count') > 0
