from fastapi.testclient import TestClient
from src.api.main import app

def test_cors():
    with TestClient(app) as client:
        # Request from allowed origin
        response = client.options("/api/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        assert response.status_code == 200

        # Request from disallowed origin
        response = client.options("/api/health", headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "GET"
        })
        assert response.status_code == 400
