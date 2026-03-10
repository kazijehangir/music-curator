import pytest
from unittest.mock import MagicMock, patch
import json
from src.services.tagging import _pass_1_beets, _pass_2_sidecars, _pass_3_llm, run_tagging, process_release

@pytest.fixture
def mock_httpx():
    with patch("src.services.tagging.httpx.post") as mock_post:
        yield mock_post

def test_pass_2_sidecars(mock_pocketbase, fs):
    # Setup realistic file structure
    fs.create_file("/test/song.opus", contents="binary data")
    fs.create_file("/test/song.info.json", contents=json.dumps({
        "track": "Test Track Name",
        "artist": "Test Artist Name"
    }))
    
    file_record = MagicMock()
    file_record.id = "file123"
    file_record.file_path = "/test/song.opus"
    
    _pass_2_sidecars(mock_pocketbase, "rel123", [file_record])
    
    # Verify PocketBase was called to create metadata source records
    assert mock_pocketbase.collection.return_value.create.call_count == 2
    calls = mock_pocketbase.collection.return_value.create.call_args_list
    
    # We don't guarantee order, so check if title and artist were created
    fields_created = [c[0][0]["field_name"] for c in calls]
    assert "title" in fields_created
    assert "artist" in fields_created

def test_pass_3_llm(mock_pocketbase, mock_httpx):
    mock_post_resp = MagicMock()
    # Provide a simulated LLM JSON response
    mock_post_resp.json.return_value = {
        "choices": [{
            "message": {
                "content": '```json\n{"title": "Cleaned Title", "artist": "Cleaned Artist", "album": null, "genre": "Pop", "language": "urd"}\n```'
            }
        }]
    }
    mock_httpx.return_value = mock_post_resp
    
    file_record = MagicMock()
    file_record.id = "file123"
    file_record.raw_title__raw_artist__raw_album = "Messy Title | Messy Artist | "
    
    stats = {"llm_processed": 0}
    _pass_3_llm(mock_pocketbase, "rel123", file_record, stats)
    
    # Called for 4 fields (title, artist, genre, language - album is null)
    assert mock_pocketbase.collection.return_value.create.call_count == 4
    assert stats["llm_processed"] == 1

def test_pass_1_beets_command_injection(mocker):
    # Mock subprocess.run to avoid actual execution
    mock_run = mocker.patch("src.services.tagging.subprocess.run")

    # Mock mutagen.File to return None so it doesn't crash trying to read the file
    mocker.patch("src.services.tagging.mutagen.File", return_value=None)

    file_record = MagicMock()
    # Path that looks like a flag
    file_record.file_path = "-s malicious_arg"

    _pass_1_beets(file_record)

    # Check that subprocess.run was called with '--' before the file path
    assert mock_run.call_count == 1
    args, kwargs = mock_run.call_args
    cmd = args[0]

    assert cmd[-2] == "--"
    assert cmd[-1] == "-s malicious_arg"
