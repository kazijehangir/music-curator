import os
import pytest
from fastapi.testclient import TestClient

# Must set env vars before importing app
os.environ["POCKETBASE_ADMIN_EMAIL"] = "admin@example.com"
os.environ["POCKETBASE_ADMIN_PASSWORD"] = "password123"
os.environ["NAS_MOUNT_PATH"] = "/mnt/nas"
os.environ["INGEST_BASE_PATH"] = "/mnt/nas/ingest"
os.environ["MEDIA_LIBRARY_PATH"] = "/mnt/nas/library"

from src.api.main import app

client = TestClient(app)

def test_cors_allowed_origin():
    response = client.options("/api/discover", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_cors_disallowed_origin():
    response = client.options("/api/discover", headers={"Origin": "http://evil.com", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 400
    assert response.text == "Disallowed CORS origin"
