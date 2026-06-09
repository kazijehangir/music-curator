from src.core.config import Settings

def test_cors_origins_list():
    settings = Settings(
        pocketbase_admin_email="a",
        pocketbase_admin_password="b",
        nas_mount_path="c",
        ingest_base_path="d",
        media_library_path="e",
        cors_allowed_origins=["http://a.com", "http://b.com"]
    )
    assert settings.cors_allowed_origins == ["http://a.com", "http://b.com"]

def test_cors_origins_str_comma_separated():
    settings = Settings(
        pocketbase_admin_email="a",
        pocketbase_admin_password="b",
        nas_mount_path="c",
        ingest_base_path="d",
        media_library_path="e",
        cors_allowed_origins="http://a.com, http://b.com "
    )
    assert settings.cors_allowed_origins == ["http://a.com", "http://b.com"]

def test_cors_origins_str_json_valid():
    settings = Settings(
        pocketbase_admin_email="a",
        pocketbase_admin_password="b",
        nas_mount_path="c",
        ingest_base_path="d",
        media_library_path="e",
        cors_allowed_origins='["http://a.com", "http://b.com"]'
    )
    assert settings.cors_allowed_origins == ["http://a.com", "http://b.com"]

def test_cors_origins_str_json_invalid():
    settings = Settings(
        pocketbase_admin_email="a",
        pocketbase_admin_password="b",
        nas_mount_path="c",
        ingest_base_path="d",
        media_library_path="e",
        cors_allowed_origins='["http://a.com"'
    )
    assert settings.cors_allowed_origins == '["http://a.com"'
