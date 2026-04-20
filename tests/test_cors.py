import pytest
from fastapi.testclient import TestClient
from src.api.main import app

def test_cors_allowed_origin():
    """Test that requests from allowed origins include CORS headers."""
    client = TestClient(app)
    headers = {
        "Origin": "http://localhost:8090",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8090"

def test_cors_disallowed_origin():
    """Test that requests from disallowed origins do not include CORS headers."""
    client = TestClient(app)
    headers = {
        "Origin": "http://evil-domain.com",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/health", headers=headers)
    assert response.status_code == 400
    assert response.headers.get("access-control-allow-origin") is None
