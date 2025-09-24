from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_endpoint_returns_pong():
    response = client.get("/broken_ping_service")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}
