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

@patch("src.services.tagging.process_release")
def test_run_tagging_prefetch(mock_process_release, mock_pocketbase):
    # Create two releases
    r1 = MagicMock()
    r1.id = "rel1"
    r2 = MagicMock()
    r2.id = "rel2"

    # Create files referencing these releases
    f1 = MagicMock()
    f1.release = "rel1"
    f2 = MagicMock()
    f2.release = "rel2"

    def dynamic_mock_get_full_list(*args, **kwargs):
        query_params = kwargs.get("query_params", {})
        filter_str = query_params.get("filter", "")
        # Mock release fetch
        if "mb_status" in filter_str:
            return [r1, r2]
        # Mock prefetch files fetch
        elif "release=" in filter_str:
            return [f1, f2]
        return []

    mock_pocketbase.collection.return_value.get_full_list.side_effect = dynamic_mock_get_full_list
    mock_process_release.return_value = True

    stats = run_tagging(mock_pocketbase)

    assert stats["tagged"] == 2
    assert mock_process_release.call_count == 2
    # Verify the chunked prefetch was called
    # One call for releases, one call for prefetching the 2 files
    assert mock_pocketbase.collection.return_value.get_full_list.call_count == 2

def test_run_tagging_fetch_releases_error(mock_pocketbase):
    mock_pocketbase.collection.return_value.get_full_list.side_effect = Exception("DB down")
    stats = run_tagging(mock_pocketbase)
    assert "DB down" in stats["errors"][0]

@patch("src.services.tagging.process_release")
def test_run_tagging_prefetch_files_error(mock_process_release, mock_pocketbase):
    r1 = MagicMock()
    r1.id = "rel1"

    def dynamic_mock_get_full_list(*args, **kwargs):
        filter_str = kwargs.get("query_params", {}).get("filter", "")
        if "mb_status" in filter_str:
            return [r1]
        elif "release=" in filter_str:
            raise Exception("Prefetch error mock")
        return []

    mock_pocketbase.collection.return_value.get_full_list.side_effect = dynamic_mock_get_full_list
    mock_process_release.return_value = True

    stats = run_tagging(mock_pocketbase)
    assert any("Prefetch error mock" in err for err in stats["errors"])

@patch("src.services.tagging.process_release")
def test_run_tagging_process_error(mock_process_release, mock_pocketbase):
    r1 = MagicMock()
    r1.id = "rel1"

    def dynamic_mock_get_full_list(*args, **kwargs):
        filter_str = kwargs.get("query_params", {}).get("filter", "")
        if "mb_status" in filter_str:
            return [r1]
        return []

    mock_pocketbase.collection.return_value.get_full_list.side_effect = dynamic_mock_get_full_list
    mock_process_release.side_effect = Exception("Process error mock")

    stats = run_tagging(mock_pocketbase)
    assert any("Process error mock" in err for err in stats["errors"])

def test_run_tagging_no_pb(mock_pocketbase):
    with patch("src.services.discover.get_pb_client", return_value=mock_pocketbase):
        mock_pocketbase.collection.return_value.get_full_list.return_value = []
        stats = run_tagging()
        assert stats["tagged"] == 0
