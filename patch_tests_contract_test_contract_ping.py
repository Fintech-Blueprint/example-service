
# This is a minimal contract test that verifies the OpenAPI contains /v1/ping
# In CI this should point to the running test server; here we check local app via TestClient or start server.
from fastapi.testclient import TestClient
from src.application.main import app

client = TestClient(app)


def test_contract_ping_path():
    # ensure the path exists by calling the endpoint
    r = client.get('/v1/ping')
    assert r.status_code == 200