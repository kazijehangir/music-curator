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

def test_run_tagging_prefetching_success(mock_pocketbase, mocker):
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pocketbase)

    # Mock process_release to just return True without doing the real passes
    mocker.patch("src.services.tagging.process_release", return_value=True)

    release1 = MagicMock()
    release1.id = "rel1"
    release2 = MagicMock()
    release2.id = "rel2"

    file1 = MagicMock()
    file1.release = "rel1"
    file2 = MagicMock()
    file2.release = "rel2"

    def mock_get_full_list(**kwargs):
        if 'query_params' in kwargs:
            filter_str = kwargs['query_params'].get('filter', '')
            if 'mb_status' in filter_str or 'needs_review' in filter_str:
                return [release1, release2]
            if "rel1" in filter_str or "rel2" in filter_str:
                return [file1, file2]
        return []

    mock_pocketbase.collection.return_value.get_full_list.side_effect = mock_get_full_list

    stats = run_tagging(mock_pocketbase)

    assert stats["tagged"] == 2
    assert "errors" in stats
    assert len(stats["errors"]) == 0

    # Ensure get_full_list for COLL_FILE was called with the combined filter
    calls = mock_pocketbase.collection.return_value.get_full_list.call_args_list
    assert len(calls) == 2
    # The first call is for releases, the second is for the prefetched files chunk
    file_query_call = calls[1]
    assert "query_params" in file_query_call[1]
    assert "rel1" in file_query_call[1]["query_params"]["filter"]
    assert "rel2" in file_query_call[1]["query_params"]["filter"]


def test_run_tagging_prefetching_error(mock_pocketbase, mocker):
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pocketbase)
    mocker.patch("src.services.tagging.process_release", return_value=False)

    release1 = MagicMock()
    release1.id = "rel1"

    def mock_get_full_list(**kwargs):
        if 'query_params' in kwargs:
            filter_str = kwargs['query_params'].get('filter', '')
            if 'mb_status' in filter_str or 'needs_review' in filter_str:
                return [release1]
            # Simulate a failure during prefetch
            raise Exception("Prefetch error")
        return []

    mock_pocketbase.collection.return_value.get_full_list.side_effect = mock_get_full_list

    stats = run_tagging(mock_pocketbase)
    assert len(stats["errors"]) == 1
    assert "Prefetch error" in stats["errors"][0]


def test_process_release_uses_prefetched_files(mock_pocketbase, mocker):
    mocker.patch("src.services.tagging._pass_0_file_tags")
    mocker.patch("src.services.tagging._pass_1_beets", return_value="mbid123")
    mocker.patch("src.services.tagging._pass_2_sidecars")
    mocker.patch("src.services.tagging._pass_3_llm")
    mocker.patch("src.services.tagging._resolve_and_write_tags")

    release = MagicMock()
    release.id = "rel123"
    file_record = MagicMock()
    file_record.id = "file1"

    stats = {"mb_matched": 0, "errors": []}

    # We pass prefetched_files so it shouldn't query COLL_FILE
    result = process_release(mock_pocketbase, release, stats, prefetched_files=[file_record])

    assert result is True
    # Verify no get_full_list query was made by process_release
    mock_pocketbase.collection.return_value.get_full_list.assert_not_called()
    assert stats["mb_matched"] == 1
