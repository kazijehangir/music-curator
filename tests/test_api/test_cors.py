def test_cors_preflight_allowed(client):
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://127.0.0.1:8090",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:8090"

def test_cors_preflight_disallowed(client):
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 400

def test_cors_request_allowed(client):
    response = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_cors_request_disallowed(client):
    response = client.get(
        "/api/health",
        headers={"Origin": "http://evil.com"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
