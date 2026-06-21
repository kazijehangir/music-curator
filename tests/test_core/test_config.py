import pytest
from src.core.config import Settings

def test_cors_config_json_parsing():
    s = Settings(
        pocketbase_admin_email="test",
        pocketbase_admin_password="test",
        nas_mount_path="/tmp",
        ingest_base_path="/tmp",
        media_library_path="/tmp",
        cors_allowed_origins='["http://foo.com", "http://bar.com"]'
    )
    assert s.cors_allowed_origins == ["http://foo.com", "http://bar.com"]

def test_cors_config_comma_parsing():
    s = Settings(
        pocketbase_admin_email="test",
        pocketbase_admin_password="test",
        nas_mount_path="/tmp",
        ingest_base_path="/tmp",
        media_library_path="/tmp",
        cors_allowed_origins='http://foo.com, http://bar.com'
    )
    assert s.cors_allowed_origins == ["http://foo.com", "http://bar.com"]

def test_cors_config_list_parsing():
    s = Settings(
        pocketbase_admin_email="test",
        pocketbase_admin_password="test",
        nas_mount_path="/tmp",
        ingest_base_path="/tmp",
        media_library_path="/tmp",
        cors_allowed_origins=["http://foo.com", "http://bar.com"]
    )
    assert s.cors_allowed_origins == ["http://foo.com", "http://bar.com"]

def test_cors_config_default_list_parsing():
    s = Settings(
        pocketbase_admin_email="test",
        pocketbase_admin_password="test",
        nas_mount_path="/tmp",
        ingest_base_path="/tmp",
        media_library_path="/tmp",
    )
    assert isinstance(s.cors_allowed_origins, list)
    assert s.cors_allowed_origins == ["http://127.0.0.1:8090", "http://localhost:3000"]
