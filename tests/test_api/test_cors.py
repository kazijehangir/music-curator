from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_cors_allowed_origin():
    response = client.options("/api/discover", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST"
    })
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_cors_disallowed_origin():
    response = client.options("/api/discover", headers={
        "Origin": "http://evil.com",
        "Access-Control-Request-Method": "POST"
    })
    assert response.status_code == 400
    assert response.text == "Disallowed CORS origin"
