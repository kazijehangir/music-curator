import pytest
from fastapi.testclient import TestClient
from src.api.main import app

def test_cors_middleware_allowed_origin():
    """
    Test that a configured CORS origin (e.g. http://localhost:3000)
    receives the appropriate Access-Control-Allow-Origin header.
    """
    with TestClient(app) as client:
        # Pre-flight request
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_cors_middleware_disallowed_origin():
    """
    Test that a disallowed CORS origin does not receive
    the Access-Control-Allow-Origin header.
    """
    with TestClient(app) as client:
        # Pre-flight request
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://evil-attacker.com",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers