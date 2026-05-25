def test_cors_preflight_disallowed_origin(client):
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://malicious.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 400
    assert response.text == "Disallowed CORS origin"

def test_cors_normal_request_disallowed_origin(client):
    response = client.get("/api/health", headers={"Origin": "http://malicious.com"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers

def test_cors_preflight_allowed_origin(client):
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_cors_normal_request_allowed_origin(client):
    response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
