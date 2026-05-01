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

def test_run_tagging(mock_pocketbase):
    # Setup mock to return a chunk of 2 releases
    mock_pb_client = mock_pocketbase
    mock_pb_client.collection.return_value.get_full_list.side_effect = [
        [MagicMock(id="rel1"), MagicMock(id="rel2")], # releases
        [MagicMock(id="file1", release="rel1"), MagicMock(id="file2", release="rel2")] # chunk files
    ]

    with patch("src.services.tagging.process_release") as mock_process_release:
        mock_process_release.return_value = True
        stats = run_tagging(mock_pb_client)
        assert stats["tagged"] == 2
        assert mock_process_release.call_count == 2

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

def test_run_tagging_empty(mock_pocketbase):
    # Setup mock to return empty releases
    mock_pb_client = mock_pocketbase
    mock_pb_client.collection.return_value.get_full_list.return_value = []

    with patch("src.services.tagging.process_release") as mock_process_release:
        stats = run_tagging(mock_pb_client)
        assert stats["tagged"] == 0
        assert mock_process_release.call_count == 0

def test_run_tagging_exception(mock_pocketbase):
    # Setup mock to raise Exception when fetching releases
    mock_pb_client = mock_pocketbase
    mock_pb_client.collection.return_value.get_full_list.side_effect = Exception("Test Exception")

    with patch("src.services.tagging.process_release") as mock_process_release:
        stats = run_tagging(mock_pb_client)
        assert stats["tagged"] == 0
        assert len(stats["errors"]) == 1
        assert "Test Exception" in stats["errors"][0]
        assert mock_process_release.call_count == 0

def test_run_tagging_process_exception(mock_pocketbase):
    # Setup mock to raise exception inside loop
    mock_pb_client = mock_pocketbase
    mock_pb_client.collection.return_value.get_full_list.side_effect = [
        [MagicMock(id="rel1")], # releases
        [MagicMock(id="file1", release="rel1")] # chunk files
    ]

    with patch("src.services.tagging.process_release") as mock_process_release:
        mock_process_release.side_effect = Exception("Process Exception")
        stats = run_tagging(mock_pb_client)
        assert stats["tagged"] == 0
        assert len(stats["errors"]) == 1
        assert "Process Exception" in stats["errors"][0]

def test_run_tagging_prefetch_exception(mock_pocketbase):
    mock_pb_client = mock_pocketbase
    mock_pb_client.collection.return_value.get_full_list.side_effect = [
        [MagicMock(id="rel1")], # releases
        Exception("Prefetch Exception") # chunk files exception
    ]

    with patch("src.services.tagging.process_release") as mock_process_release:
        stats = run_tagging(mock_pb_client)
        assert stats["tagged"] == 0
        assert len(stats["errors"]) == 1
        assert "Prefetch Exception" in stats["errors"][0]

def test_process_release_no_files(mock_pocketbase):
    mock_pb_client = mock_pocketbase
    release = MagicMock(id="rel1")
    stats = {"tagged": 0, "mb_matched": 0, "llm_processed": 0, "errors": []}

    # Passing pre_fetched_files=[]
    result = process_release(mock_pb_client, release, stats, [])
    assert result is False

def test_process_release_with_files(mock_pocketbase):
    mock_pb_client = mock_pocketbase
    release = MagicMock(id="rel1")
    stats = {"tagged": 0, "mb_matched": 0, "llm_processed": 0, "errors": []}
    file1 = MagicMock(id="file1", is_primary=True)

    with patch("src.services.tagging._pass_0_file_tags") as mock_p0, \
         patch("src.services.tagging._pass_1_beets") as mock_p1, \
         patch("src.services.tagging._pass_2_sidecars") as mock_p2, \
         patch("src.services.tagging._pass_3_llm") as mock_p3, \
         patch("src.services.tagging._resolve_and_write_tags") as mock_resolve:

         mock_p1.return_value = "mbid123"
         result = process_release(mock_pb_client, release, stats, [file1])
         assert result is True
         mock_p0.assert_called_once()
         mock_p1.assert_called_once()
         mock_p2.assert_called_once()
         mock_p3.assert_not_called() # skipped due to mb_id
         mock_resolve.assert_called_once()


def test_process_release_without_pre_fetched_files(mock_pocketbase):
    mock_pb_client = mock_pocketbase
    release = MagicMock(id="rel1")
    stats = {"tagged": 0, "mb_matched": 0, "llm_processed": 0, "errors": []}
    file1 = MagicMock(id="file1", is_primary=True)

    mock_pb_client.collection.return_value.get_full_list.return_value = [file1]

    with patch("src.services.tagging._pass_0_file_tags") as mock_p0, \
         patch("src.services.tagging._pass_1_beets") as mock_p1, \
         patch("src.services.tagging._pass_2_sidecars") as mock_p2, \
         patch("src.services.tagging._pass_3_llm") as mock_p3, \
         patch("src.services.tagging._resolve_and_write_tags") as mock_resolve:

         mock_p1.return_value = None
         result = process_release(mock_pb_client, release, stats, None)
         assert result is True
         mock_p3.assert_called_once()

def test_process_release_no_pre_fetched_files_returns_false(mock_pocketbase):
    mock_pb_client = mock_pocketbase
    release = MagicMock(id="rel1")
    stats = {"tagged": 0, "mb_matched": 0, "llm_processed": 0, "errors": []}

    mock_pb_client.collection.return_value.get_full_list.return_value = []

    result = process_release(mock_pb_client, release, stats, None)
    assert result is False

def test_run_tagging_no_pb():
    with patch("src.services.discover.get_pb_client") as mock_get_pb:
        mock_pb_client = MagicMock()
        mock_get_pb.return_value = mock_pb_client
        mock_pb_client.collection.return_value.get_full_list.return_value = []
        stats = run_tagging(None)
        assert stats["tagged"] == 0


def test_pass_0_file_tags(mock_pocketbase):
    from src.services.tagging import _pass_0_file_tags, CONF_FILE_TAGS, CONF_SIDECAR, CONF_ADHOC
    mock_pb_client = mock_pocketbase
    release_id = "rel1"

    # tidal-dl file
    file1 = MagicMock(id="file1")
    file1.raw_title__raw_artist__raw_album = "Title1 | Artist1 | Album1"
    file1.source_dir = "tidal-dl"

    # yubal file
    file2 = MagicMock(id="file2")
    file2.raw_title__raw_artist__raw_album = "Title2 | Artist2 | Album2"
    file2.source_dir = "yubal"

    # adhoc file
    file3 = MagicMock(id="file3")
    file3.raw_title__raw_artist__raw_album = "Title3 | Artist3 | Album3"
    file3.source_dir = "adhoc"

    # Missing combo file
    file4 = MagicMock(id="file4")
    file4.raw_title__raw_artist__raw_album = None
    file4.source_dir = "tidal-dl"

    _pass_0_file_tags(mock_pb_client, release_id, [file1, file2, file3, file4])

    assert mock_pb_client.collection.return_value.create.call_count == 9

def test_pass_1_beets(mock_pocketbase):
    from src.services.tagging import _pass_1_beets

    file_record = MagicMock(id="file1", file_path="/tmp/song.flac")

    with patch("src.services.tagging.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch("src.services.tagging.mutagen.File") as mock_mutagen:
            mock_f = MagicMock()
            mock_mutagen.return_value = mock_f
            mock_f.__contains__.side_effect = lambda key: key == "musicbrainz_trackid"
            mock_f.__getitem__.side_effect = lambda key: ["mbid123"] if key == "musicbrainz_trackid" else None

            mb_id = _pass_1_beets(file_record)
            assert mb_id == "mbid123"

def test_pass_1_beets_no_mbid(mock_pocketbase):
    from src.services.tagging import _pass_1_beets

    file_record = MagicMock(id="file1", file_path="/tmp/song.flac")

    with patch("src.services.tagging.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout='{"other_key": "val"}')
        mb_id = _pass_1_beets(file_record)
        assert mb_id is None

def test_pass_1_beets_failure(mock_pocketbase):
    from src.services.tagging import _pass_1_beets

    file_record = MagicMock(id="file1", file_path="/tmp/song.flac")

    with patch("src.services.tagging.subprocess.run") as mock_run:
        mock_run.side_effect = Exception("Beets Exception")
        mb_id = _pass_1_beets(file_record)
        assert mb_id is None

def test_resolve_and_write_tags(mock_pocketbase):
    from src.services.tagging import _resolve_and_write_tags

    mock_pb_client = mock_pocketbase
    release_id = "rel1"
    primary_file = MagicMock(id="file1", file_path="/tmp/song.flac")

    mock_pb_client.collection.return_value.get_full_list.return_value = [
        MagicMock(field_name="title", value="Title1", confidence=50),
        MagicMock(field_name="title", value="Title2", confidence=80),
        MagicMock(field_name="artist", value="Artist1", confidence=60),
    ]

    with patch("src.services.tagging._write_mutagen_tags") as mock_write_tags:
        _resolve_and_write_tags(mock_pb_client, release_id, primary_file)

        mock_pb_client.collection.return_value.update.assert_called_once_with("rel1", {"title": "Title2", "artist": "Artist1"})
        mock_write_tags.assert_called_once_with("/tmp/song.flac", {"title": "Title2", "artist": "Artist1"})

def test_resolve_and_write_tags_exception(mock_pocketbase):
    from src.services.tagging import _resolve_and_write_tags

    mock_pb_client = mock_pocketbase
    release_id = "rel1"
    primary_file = MagicMock(id="file1", file_path="/tmp/song.flac")

    mock_pb_client.collection.return_value.get_full_list.side_effect = Exception("Fetch Exception")

    with patch("src.services.tagging._write_mutagen_tags") as mock_write_tags:
        _resolve_and_write_tags(mock_pb_client, release_id, primary_file)
        mock_pb_client.collection.return_value.update.assert_not_called()
        mock_write_tags.assert_not_called()

def test_write_mutagen_tags():
    from src.services.tagging import _write_mutagen_tags

    tags = {"title": "New Title", "artist": "New Artist"}
    file_path = "/tmp/song.flac"

    with patch("src.services.tagging.mutagen.File") as mock_mutagen_file:
        mock_f = MagicMock()
        mock_mutagen_file.return_value = mock_f

        _write_mutagen_tags(file_path, tags)

        mock_f.__setitem__.assert_any_call("title", "New Title")
        mock_f.__setitem__.assert_any_call("artist", "New Artist")
        mock_f.save.assert_called_once()

def test_write_mutagen_tags_exception():
    from src.services.tagging import _write_mutagen_tags

    tags = {"title": "New Title"}
    file_path = "/tmp/song.flac"

    with patch("src.services.tagging.mutagen.File") as mock_mutagen_file:
        mock_mutagen_file.side_effect = Exception("Mutagen Exception")

        # should not raise
        _write_mutagen_tags(file_path, tags)
