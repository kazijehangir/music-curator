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
    assert data["status"] == "accepted"
