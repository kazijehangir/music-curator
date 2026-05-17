def test_cors_preflight_allowed(client):
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://127.0.0.1:8090",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:8090"

def test_cors_preflight_disallowed(client):
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 400

def test_cors_request_allowed(client):
    response = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_cors_request_disallowed(client):
    response = client.get(
        "/api/health",
        headers={"Origin": "http://evil.com"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers

def test_cors_config_assemble_from_string():
    from src.core.config import Settings
    import os
    os.environ["CORS_ALLOWED_ORIGINS"] = "http://test1.com, http://test2.com ,http://test3.com"
    os.environ["POCKETBASE_ADMIN_EMAIL"] = "test@test.com"
    os.environ["POCKETBASE_ADMIN_PASSWORD"] = "password"
    os.environ["NAS_MOUNT_PATH"] = "/tmp/nas"
    os.environ["INGEST_BASE_PATH"] = "/tmp/ingest"
    os.environ["MEDIA_LIBRARY_PATH"] = "/tmp/media"

    settings = Settings()
    assert settings.cors_allowed_origins == ["http://test1.com", "http://test2.com", "http://test3.com"]

    del os.environ["CORS_ALLOWED_ORIGINS"]

def test_cors_config_assemble_from_list():
    from src.core.config import Settings
    import os
    os.environ["POCKETBASE_ADMIN_EMAIL"] = "test@test.com"
    os.environ["POCKETBASE_ADMIN_PASSWORD"] = "password"
    os.environ["NAS_MOUNT_PATH"] = "/tmp/nas"
    os.environ["INGEST_BASE_PATH"] = "/tmp/ingest"
    os.environ["MEDIA_LIBRARY_PATH"] = "/tmp/media"

    settings = Settings(cors_allowed_origins=["http://test1.com", "http://test2.com"])
    assert settings.cors_allowed_origins == ["http://test1.com", "http://test2.com"]
