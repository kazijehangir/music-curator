"""API-level smoke tests for POST /api/analyze."""
import pytest


async def _stream_success(*args, **kwargs):
    yield "Task started: /api/analyze (PID: 1234, PGID: 1234)\n"
    yield "STATUS: Analyzed 3 files, 2 new releases, 1 merged.\n"
    yield "Task /api/analyze finished with code 0\n"


async def _stream_with_error(*args, **kwargs):
    yield "Task started: /api/analyze (PID: 1234, PGID: 1234)\n"
    yield "ERROR: File not found on disk: /mnt/music/missing.flac\n"
    yield "Task /api/analyze finished with code 1\n"


def test_post_analyze_success(client, mocker):
    """POST /api/analyze returns 200 with streaming text output."""
    mocker.patch("src.api.endpoints.task_manager.run_task", side_effect=_stream_success)

    response = client.post("/api/analyze")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "Task started" in response.text
    assert "finished with code 0" in response.text


def test_post_analyze_propagates_errors(client, mocker):
    """Error output from the subprocess is streamed back to the caller."""
    mocker.patch("src.api.endpoints.task_manager.run_task", side_effect=_stream_with_error)

    response = client.post("/api/analyze")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "ERROR:" in response.text
