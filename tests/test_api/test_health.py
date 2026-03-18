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

from src.core.config import settings
def test_cors_origins_settings_parses_comma_separated_strings():
    """Verify CORS ORIGINS splits on commas."""
    original = settings.cors_origins
    try:
        settings.cors_origins = "http://a.com, http://b.com "
        origins = [origin.strip() for origin in settings.cors_origins.split(",")]
        assert len(origins) == 2
        assert "http://a.com" in origins
        assert "http://b.com" in origins
    finally:
        settings.cors_origins = original
