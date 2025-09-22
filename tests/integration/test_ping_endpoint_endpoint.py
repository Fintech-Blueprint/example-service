import pytest
from fastapi.testclient import TestClient
from src.application.main import app

client = TestClient(app)


@pytest.mark.integration
def test_endpoint_returns_pong():
    response = client.get("/v1/ping")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json.get("pong") is True
    assert response_json.get("service") == "example-service"
    assert "commit" in response_json
