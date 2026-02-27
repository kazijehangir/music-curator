
import os
import pytest
from unittest.mock import MagicMock

# Set required environment variables BEFORE importing app or settings
os.environ["POCKETBASE_ADMIN_EMAIL"] = "admin@example.com"
os.environ["POCKETBASE_ADMIN_PASSWORD"] = "password"
os.environ["NAS_MOUNT_PATH"] = "/tmp/nas"
os.environ["INGEST_BASE_PATH"] = "/tmp/ingest"
os.environ["MEDIA_LIBRARY_PATH"] = "/tmp/library"

from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture
def client():
    # Provide a test client for simulating HTTP requests against the FastAPI app
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_pocketbase(mocker):
    # This fixture mocks out the PocketBase python client
    # to avoid hitting the actual database during unit tests.
    mock_pb = mocker.patch("pocketbase.PocketBase")
    return mock_pb.return_value

@pytest.fixture
def setup_fs(fs):
    # Create fake directory structures for testing logic without touching the actual Unraid NAS
    fs.create_dir("/mnt/user/main/downloads/unseeded/music/yubal")
    fs.create_dir("/mnt/user/main/downloads/unseeded/music/tidal-dl")
    fs.create_dir("/mnt/user/main/media/Music")
    yield fs
