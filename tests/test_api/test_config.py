import pytest
from src.core.config import Settings

def test_cors_origins_default():
    settings = Settings()
    assert isinstance(settings.cors_allowed_origins, list)
    assert "http://127.0.0.1:8090" in settings.cors_allowed_origins

def test_cors_origins_comma_separated():
    settings = Settings(cors_allowed_origins="http://example.com, https://example.org ")
    assert settings.cors_allowed_origins == ["http://example.com", "https://example.org"]

def test_cors_origins_json_list():
    settings = Settings(cors_allowed_origins='["http://example.com", "https://example.org"]')
    assert settings.cors_allowed_origins == ["http://example.com", "https://example.org"]

def test_cors_origins_json_decode_error():
    # If it starts with [ but is invalid JSON, it should return it as a single element list
    settings = Settings(cors_allowed_origins='[http://invalid.json]')
    assert settings.cors_allowed_origins == ['[http://invalid.json]']
