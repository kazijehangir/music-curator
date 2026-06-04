import pytest

async def _stream_success(*args, **kwargs):
    yield "Task started: /api/analyze (PID: 1234, PGID: 1234)\n"
    yield "STATUS: Analyzed 3 files, 2 new releases, 1 merged.\n"
    yield "Task /api/analyze finished with code 0\n"

def test_cors_origin_disallowed(client):
    """Test that a request from a disallowed origin fails the preflight check."""
    response = client.options(
        "/api/analyze",
        headers={
            "Origin": "http://evil-domain.com",
            "Access-Control-Request-Method": "POST"
        }
    )
    assert response.status_code == 400
    assert response.text == "Disallowed CORS origin"

def test_cors_origin_allowed(client, mocker):
    """Test that a request from an allowed origin passes CORS."""
    mocker.patch("src.api.endpoints.task_manager.run_task", side_effect=_stream_success)
    response = client.post(
        "/api/analyze",
        headers={
            "Origin": "http://localhost:3000"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
