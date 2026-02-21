"""API-level smoke tests for POST /api/analyze."""
import pytest


def test_post_analyze_success(client, mocker):
    """POST /api/analyze returns 200 with the expected JSON fields."""
    mocker.patch(
        "src.services.analyze.run_analysis",
        return_value={
            "analyzed": 3,
            "new_releases": 2,
            "merged_files": 1,
            "errors": [],
        },
    )

    response = client.post("/api/analyze")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["analyzed"] == 3
    assert body["new_releases"] == 2
    assert body["merged_files"] == 1
    assert body["errors"] == []


def test_post_analyze_propagates_errors(client, mocker):
    """If run_analysis returns errors, they are surfaced in the response."""
    mocker.patch(
        "src.services.analyze.run_analysis",
        return_value={
            "analyzed": 1,
            "new_releases": 0,
            "merged_files": 0,
            "errors": ["File not found on disk: /mnt/music/missing.flac"],
        },
    )

    response = client.post("/api/analyze")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert len(body["errors"]) == 1
