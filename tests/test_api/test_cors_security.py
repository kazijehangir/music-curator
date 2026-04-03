from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_cors_policy_allowed_origin():
    headers = {
        "Origin": "http://localhost:8090",
        "Access-Control-Request-Method": "GET"
    }
    response = client.options("/api/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8090"
    assert response.headers.get("access-control-allow-credentials") is None or response.headers.get("access-control-allow-credentials") == "false"

def test_cors_policy_disallowed_origin():
    headers = {
        "Origin": "http://malicious.com",
        "Access-Control-Request-Method": "GET"
    }
    response = client.options("/api/health", headers=headers)
    assert response.status_code == 400
    assert response.headers.get("access-control-allow-origin") is None
