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

def test_run_tagging_prefetches_files(mock_pocketbase):
    # Setup releases
    rel1 = MagicMock()
    rel1.id = "rel1"
    rel2 = MagicMock()
    rel2.id = "rel2"

    mock_pocketbase.collection.return_value.get_full_list.side_effect = [
        [rel1, rel2], # First call: get releases
        # Second call: prefetch files chunk 1
        [MagicMock(release="rel1", id="file1"), MagicMock(release="rel2", id="file2")]
    ]

    with patch("src.services.tagging.process_release") as mock_process:
        mock_process.return_value = True
        run_tagging(mock_pocketbase)

        # Verify process_release was called with the prefetched files
        assert mock_process.call_count == 2

        # First call args
        args_1 = mock_process.call_args_list[0][0]
        kwargs_1 = mock_process.call_args_list[0][1]
        assert args_1[1].id == "rel1"
        assert len(kwargs_1["prefetched_files"]) == 1
        assert kwargs_1["prefetched_files"][0].id == "file1"

        # Second call args
        args_2 = mock_process.call_args_list[1][0]
        kwargs_2 = mock_process.call_args_list[1][1]
        assert args_2[1].id == "rel2"
        assert len(kwargs_2["prefetched_files"]) == 1
        assert kwargs_2["prefetched_files"][0].id == "file2"

def test_process_release_uses_prefetched_files(mock_pocketbase):
    rel = MagicMock()
    rel.id = "rel1"

    file1 = MagicMock(release="rel1", id="file1")
    file1.is_primary = True

    with patch("src.services.tagging._pass_0_file_tags"), \
         patch("src.services.tagging._pass_1_beets", return_value=None), \
         patch("src.services.tagging._pass_2_sidecars"), \
         patch("src.services.tagging._pass_3_llm"), \
         patch("src.services.tagging._resolve_and_write_tags"):

        # Run process_release with prefetched files
        stats = {}
        process_release(mock_pocketbase, rel, stats, prefetched_files=[file1])

        # Verify get_full_list was not called
        mock_pocketbase.collection.return_value.get_full_list.assert_not_called()
