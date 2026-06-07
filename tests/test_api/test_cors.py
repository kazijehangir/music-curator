from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_cors_preflight_allowed():
    response = client.options(
        "/api/discover",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Requested-With"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_cors_preflight_disallowed():
    response = client.options(
        "/api/discover",
        headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Requested-With"
        }
    )
    assert response.status_code == 400
    assert response.text == "Disallowed CORS origin"

def test_cors_normal_request_disallowed_origin_omits_header(mocker):
    mocker.patch("src.api.endpoints.task_manager.run_task")
    response = client.post(
        "/api/discover",
        headers={"Origin": "http://evil.com"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
