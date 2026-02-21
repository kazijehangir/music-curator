import pytest
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
