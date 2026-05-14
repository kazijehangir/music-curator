from fastapi.testclient import TestClient
from src.api.main import app
from src.core.config import settings

client = TestClient(app)

def test_cors_allowed_origin():
    assert len(settings.cors_origins) > 0
    allowed_origin = settings.cors_origins[0]
    response = client.options(
        "/api/health",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == allowed_origin
    assert response.headers.get("access-control-allow-credentials") != "true"

def test_cors_disallowed_origin():
    disallowed_origin = "http://malicious.com"
    response = client.options(
        "/api/health",
        headers={
            "Origin": disallowed_origin,
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 400
    assert response.headers.get("access-control-allow-origin") is None
