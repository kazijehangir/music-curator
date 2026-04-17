def test_cors_options_request(client):
    """Verify that CORS is correctly configured based on settings."""
    # Based on the fixture in tests/conftest.py which uses the FastAPI app.
    # The CORS_ORIGINS is parsed from the environment.
    # Since we cannot easily overwrite settings after app initialization in TestClient without a complex setup,
    # we just send an OPTIONS request from an allowed origin if it exists, but usually we can check CORS headers.
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    }
    response = client.options("/api/health", headers=headers)
    assert response.status_code == 200
    # The server should echo back the origin if it matches the CORS settings.
    # If the tests are run with CORS_ORIGINS=http://localhost:3000, this will match.
    assert "access-control-allow-origin" in response.headers


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "broken_symlinks" in data
    assert data["message"] == "Health skeleton"

def test_discover_streams_text(client, mocker):
    """POST /api/discover returns streaming plain text via the task manager."""
    async def mock_stream(*args, **kwargs):
        yield "Task started: /api/discover (PID: 1234, PGID: 1234)\n"
        yield "STATUS: Found 0 new files.\n"
        yield "Task /api/discover finished with code 0\n"

    mocker.patch("src.api.endpoints.task_manager.run_task", side_effect=mock_stream)

    response = client.post("/api/discover")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "finished with code" in response.text
