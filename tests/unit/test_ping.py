from fastapi.testclient import TestClient
from src.application.main import app

client = TestClient(app)

def test_ping():
    r = client.get('/v1/ping')
    assert r.status_code == 200
    j = r.json()
    assert j.get('pong') is True
