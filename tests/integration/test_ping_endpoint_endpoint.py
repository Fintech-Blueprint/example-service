import pytest
from fastapi.testclient import TestClient
from prometheus_client import CONTENT_TYPE_LATEST
from src.application.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.integration
def test_ping_endpoint_health_check(client):
    """Test the /v1/ping endpoint returns health check data."""
    response = client.get("/v1/ping")
    assert response.status_code == 200
    data = response.json()
    
    # Validate response structure
    assert data["status"] == "healthy"
    assert data["message"] == "pong"
    assert isinstance(data["uptime_seconds"], (int, float))
    assert "timestamp" in data

@pytest.mark.integration
def test_metrics_endpoint_prometheus_format(client):
    """Test the /v1/metrics endpoint returns Prometheus metrics."""
    # Make a ping request first to generate some metrics
    client.get("/v1/ping")
    
    # Check metrics endpoint
    response = client.get("/v1/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == CONTENT_TYPE_LATEST
    
    # Validate metrics content
    metrics = response.text
    required_metrics = [
        'ping_requests_total',
        'ping_latency_seconds',
        'ping_last_success_timestamp',
        'ping_health_status',
        # Dependency metrics from dependency_manager.py
        'service_dependency_health',
        'service_dependency_mode'
    ]
    
    for metric in required_metrics:
        assert metric in metrics
