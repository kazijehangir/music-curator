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

def test_pass_1_beets(mock_pocketbase, mocker, fs):
    from src.services.tagging import _pass_1_beets

    fs.create_file("/test/-song.flac", contents="binary data")

    file_record = MagicMock()
    file_record.id = "file123"
    file_record.file_path = "/test/-song.flac"

    mock_run = mocker.patch("src.services.tagging.subprocess.run")
    mock_mutagen = mocker.patch("src.services.tagging.mutagen.File")

    # Simulate mutagen finding a tag
    mock_f = MagicMock()
    mock_f.__contains__.return_value = True
    mock_f.__getitem__.return_value = ["mbid-1234"]
    mock_mutagen.return_value = mock_f

    mbid = _pass_1_beets(file_record)

    assert mbid == "mbid-1234"
    mock_run.assert_called_once()

    # Assert that '--' was passed before the file path
    cmd_args = mock_run.call_args[0][0]
    assert cmd_args[-2:] == ["--", "/test/-song.flac"]
