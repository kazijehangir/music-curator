from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_cors_allowed_origin():
    response = client.get(
        "/api/health",
        headers={
            "Origin": "http://localhost",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost"

def test_cors_disallowed_origin():
    response = client.get(
        "/api/health",
        headers={
            "Origin": "http://malicious.com",
        }
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
