import pytest
from src.core.config import Settings

def test_cors_allowed_origins_string():
    settings = Settings(cors_allowed_origins="http://localhost:3000,http://127.0.0.1:8090")
    assert settings.cors_allowed_origins == ["http://localhost:3000", "http://127.0.0.1:8090"]

def test_cors_allowed_origins_list():
    settings = Settings(cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:8090"])
    assert settings.cors_allowed_origins == ["http://localhost:3000", "http://127.0.0.1:8090"]

def test_cors_allowed_origins_json_string():
    settings = Settings(cors_allowed_origins='["http://localhost:3000","http://127.0.0.1:8090"]')
    assert settings.cors_allowed_origins == ["http://localhost:3000", "http://127.0.0.1:8090"]

def test_cors_allowed_origins_invalid_type():
    with pytest.raises(ValueError):
        Settings(cors_allowed_origins=123)
