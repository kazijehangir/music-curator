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
    from src.core.schema import COLL_RELEASE, COLL_FILE, MusicFile

    release1 = MagicMock()
    release1.id = "rel1"
    release2 = MagicMock()
    release2.id = "rel2"

    # Setup files fetch
    file1 = MagicMock()
    file1.release = "rel1"
    file1.id = "file1"

    file2 = MagicMock()
    file2.release = "rel2"
    file2.id = "file2"

    coll_release_mock = MagicMock()
    coll_release_mock.get_full_list.return_value = [release1, release2]

    coll_file_mock = MagicMock()
    coll_file_mock.get_full_list.return_value = [file1, file2]

    def mock_collection(name):
        if name == COLL_RELEASE:
            return coll_release_mock
        elif name == COLL_FILE:
            return coll_file_mock
        return MagicMock()

    mock_pocketbase.collection.side_effect = mock_collection

    # Mock process_release to avoid full tagging pipeline
    mock_process_release = mocker.patch("src.services.tagging.process_release", return_value=True)

    stats = run_tagging(pb=mock_pocketbase)

    # Verify releases were fetched
    coll_release_mock.get_full_list.assert_called_once()

    # Verify files were prefetched with the right chunked filter
    assert coll_file_mock.get_full_list.call_count == 1
    filter_arg = coll_file_mock.get_full_list.call_args[1]["query_params"]["filter"]
    assert "release='rel1'" in filter_arg
    assert "release='rel2'" in filter_arg
    assert "||" in filter_arg

    # Verify process_release was called with the right prefetched files list
    assert mock_process_release.call_count == 2

    # Check arguments of the first call (for release1)
    args, kwargs = mock_process_release.call_args_list[0]
    assert args[1].id == "rel1"
    assert args[2] == [file1]

    # Check arguments of the second call (for release2)
    args, kwargs = mock_process_release.call_args_list[1]
    assert args[1].id == "rel2"
    assert args[2] == [file2]

    assert stats["tagged"] == 2
    assert stats["errors"] == []

def test_run_tagging_empty_releases(mock_pocketbase, mocker):
    from src.core.schema import COLL_RELEASE, COLL_FILE

    coll_release_mock = MagicMock()
    coll_release_mock.get_full_list.return_value = []

    coll_file_mock = MagicMock()

    def mock_collection(name):
        if name == COLL_RELEASE:
            return coll_release_mock
        elif name == COLL_FILE:
            return coll_file_mock
        return MagicMock()

    mock_pocketbase.collection.side_effect = mock_collection

    stats = run_tagging(pb=mock_pocketbase)

    assert stats["tagged"] == 0
    assert stats["errors"] == []
    coll_file_mock.get_full_list.assert_not_called()

def test_run_tagging_prefetch_error_handling(mock_pocketbase, mocker):
    from src.core.schema import COLL_RELEASE, COLL_FILE

    release1 = MagicMock()
    release1.id = "rel1"

    coll_release_mock = MagicMock()
    coll_release_mock.get_full_list.return_value = [release1]

    coll_file_mock = MagicMock()
    coll_file_mock.get_full_list.side_effect = Exception("DB error")

    def mock_collection(name):
        if name == COLL_RELEASE:
            return coll_release_mock
        elif name == COLL_FILE:
            return coll_file_mock
        return MagicMock()

    mock_pocketbase.collection.side_effect = mock_collection

    stats = run_tagging(pb=mock_pocketbase)

    assert stats["tagged"] == 0
    assert len(stats["errors"]) == 1
    assert "Failed to prefetch files" in stats["errors"][0]


def test_run_tagging_process_release_exception(mock_pocketbase, mocker):
    from src.core.schema import COLL_RELEASE, COLL_FILE

    release1 = MagicMock()
    release1.id = "rel1"

    file1 = MagicMock()
    file1.release = "rel1"
    file1.id = "file1"

    coll_release_mock = MagicMock()
    coll_release_mock.get_full_list.return_value = [release1]

    coll_file_mock = MagicMock()
    coll_file_mock.get_full_list.return_value = [file1]

    def mock_collection(name):
        if name == COLL_RELEASE:
            return coll_release_mock
        elif name == COLL_FILE:
            return coll_file_mock
        return MagicMock()

    mock_pocketbase.collection.side_effect = mock_collection

    mock_process_release = mocker.patch("src.services.tagging.process_release", side_effect=Exception("Process error"))

    stats = run_tagging(pb=mock_pocketbase)

    assert stats["tagged"] == 0
    assert len(stats["errors"]) == 1
    assert "Error tagging release rel1" in stats["errors"][0]

def test_process_release_no_files():
    from src.services.tagging import process_release
    stats = {}
    assert not process_release(None, None, [], stats)


def test_run_tagging_fetch_releases_error(mock_pocketbase, mocker):
    from src.core.schema import COLL_RELEASE

    coll_release_mock = MagicMock()
    coll_release_mock.get_full_list.side_effect = Exception("Failed fetching releases")

    def mock_collection(name):
        if name == COLL_RELEASE:
            return coll_release_mock
        return MagicMock()

    mock_pocketbase.collection.side_effect = mock_collection

    stats = run_tagging(pb=mock_pocketbase)

    assert stats["tagged"] == 0
    assert len(stats["errors"]) == 1
    assert "Failed fetching releases" in stats["errors"][0]
