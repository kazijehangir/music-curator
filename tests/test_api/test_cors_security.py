from fastapi.testclient import TestClient
from src.api.main import app

def test_cors_policy():
    client = TestClient(app)

    # Test allowed origin
    response_allowed = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:8090",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response_allowed.status_code == 200
    assert response_allowed.headers.get("access-control-allow-origin") == "http://localhost:8090"

    # Test disallowed origin
    response_disallowed = client.options(
        "/api/health",
        headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert "access-control-allow-origin" not in response_disallowed.headers

def test_cors_allow_credentials():
    client = TestClient(app)
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:8090",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert "access-control-allow-credentials" not in response.headers or response.headers.get("access-control-allow-credentials") == "false"
