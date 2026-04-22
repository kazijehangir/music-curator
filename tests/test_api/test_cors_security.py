from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_cors_allowed_origin():
    headers = {
        "Origin": "http://localhost:8090",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8090"
    assert response.headers.get("access-control-allow-credentials") != "true"

def test_cors_disallowed_origin():
    headers = {
        "Origin": "http://evil.com",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/health", headers=headers)
    assert response.status_code == 400
    assert "Disallowed CORS origin" in response.text
