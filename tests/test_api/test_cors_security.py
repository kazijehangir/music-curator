import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_cors_preflight_allowed_origin():
    """Test that an allowed origin gets the proper CORS headers."""
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:8090",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8090"
    # Starlette sets credentials to true or doesn't include it; we verify it is not true.
    assert response.headers.get("access-control-allow-credentials") != "true"

def test_cors_preflight_disallowed_origin():
    """Test that a disallowed origin does not get CORS headers."""
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "GET",
        }
    )
    # Starlette returns 400 Bad Request if the origin is not allowed for preflight.
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
