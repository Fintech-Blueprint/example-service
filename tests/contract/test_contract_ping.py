import json
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from src.application.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.contract
def test_ping_contract(client):
    """Test that /v1/ping adheres to the contract."""
    response = client.get('/v1/ping')
    assert response.status_code == 200
    data = response.json()
    
    # Validate contract schema
    required_fields = {
        "status": str,
        "message": str,
        "uptime_seconds": (int, float),
        "timestamp": str
    }
    
    for field, expected_type in required_fields.items():
        assert field in data, f"Missing required field: {field}"
        assert isinstance(data[field], expected_type), f"Wrong type for {field}"
    
    # Validate timestamp format
    timestamp = datetime.fromisoformat(data["timestamp"])
    assert timestamp.tzinfo is not None, "Timestamp must be timezone-aware"

@pytest.mark.contract
def test_metrics_contract(client):
    """Test that /v1/metrics follows Prometheus format."""
    response = client.get('/v1/metrics')
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; version=0.0.4"
    
    # Basic Prometheus format validation
    lines = response.text.split('\n')
    metrics_found = set()
    
    for line in lines:
        if line and not line.startswith('#'):
            # Extract metric name
            metric_name = line.split('{')[0].strip()
            metrics_found.add(metric_name)
    
    # Required metrics per contract
    required_metrics = {
        'ping_requests_total',
        'ping_latency_seconds',
        'ping_health_status',
        'service_dependency_health',
        'service_dependency_mode'
    }
    
    missing_metrics = required_metrics - metrics_found
    assert not missing_metrics, f"Missing required metrics: {missing_metrics}"
