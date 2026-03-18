import pytest
from unittest.mock import MagicMock, patch
import json
from src.services.tagging import _pass_2_sidecars, _pass_3_llm, run_tagging, process_release

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

from src.services.tagging import _pass_1_beets

def test_pass_1_beets_success(mock_pocketbase, fs):
    """Test that beets import is called correctly with the -- separator."""
    fs.create_file("/test/-weird-song.flac", contents="binary data")

    file_record = MagicMock()
    file_record.id = "file123"
    file_record.file_path = "/test/-weird-song.flac"

    with patch("src.services.tagging.subprocess.run") as mock_run:
        with patch("src.services.tagging.mutagen.File") as mock_mutagen:
            # Setup mutagen mock to return None so we just test the subprocess call
            mock_mutagen.return_value = None

            _pass_1_beets(file_record)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[-1] == "/test/-weird-song.flac"
            assert args[-2] == "--"
            assert mock_run.call_args[1].get("capture_output") is True

def test_pass_1_beets_failure_handled(mock_pocketbase, fs):
    """Test that beets exception is caught and logged."""
    fs.create_file("/test/song.flac", contents="binary data")
    file_record = MagicMock()
    file_record.id = "file123"
    file_record.file_path = "/test/song.flac"

    with patch("src.services.tagging.subprocess.run", side_effect=Exception("Beets crashed")):
        # Should not raise
        result = _pass_1_beets(file_record)
        assert result is None
