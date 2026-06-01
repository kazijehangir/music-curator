from src.core.config import settings

def test_cors_allowed_origin(client):
    # Get the first allowed origin
    allowed_origin = settings.cors_allowed_origins[0]
    response = client.options("/api/health", headers={"origin": allowed_origin, "access-control-request-method": "GET"})
    assert response.status_code == 200

def test_cors_disallowed_origin(client):
    response = client.options("/api/health", headers={"origin": "http://evil.com", "access-control-request-method": "GET"})
    assert response.status_code == 400
    assert response.text == "Disallowed CORS origin"
