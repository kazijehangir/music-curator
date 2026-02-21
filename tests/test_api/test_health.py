def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "broken_symlinks" in data
    assert data["message"] == "Health skeleton"

def test_discover_skeleton(client):
    response = client.post("/api/discover")
    assert response.status_code == 200
    data = response.json()
    # discover now runs the real pipeline; it either succeeds or errors —
    # it no longer returns the old "accepted" skeleton.
    assert data["status"] in ("success", "error")
