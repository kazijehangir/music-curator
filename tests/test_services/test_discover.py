import pytest
import concurrent.futures
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.services.discover import run_discovery, extract_metadata, repair_file_metadata
from src.core.schema import COLL_FILE, MusicFile

from src.core.config import settings

def test_run_discovery_skip_invalid_exts(tmp_path, mocker):
    mocker.patch.object(settings, "ingest_base_path", str(tmp_path / "downloads" / "unseeded" / "music"))
    
    # setup valid and invalid files
    yubal_dir = tmp_path / "downloads" / "unseeded" / "music" / "yubal"
    yubal_dir.mkdir(parents=True)
    yubal_dir.joinpath("song.flac").touch()
    yubal_dir.joinpath("song.txt").touch()

    # Mock stat_fingerprint and extract_metadata since files are empty
    mocker.patch("src.services.discover.stat_fingerprint", return_value="12345:67890")
    mocker.patch("src.services.discover.extract_metadata", return_value={
        "codec": "flac",
        "sample_rate": 44100,
        "bit_depth": 16,
        "bitrate": 1411,
        "duration_seconds": 180,
        "title": "Fake Title",
        "artist": "Fake Artist",
        "album": "Fake Album"
    })

    # mock get_pb_client locally to return dummy structure
    mock_pb_client = mocker.MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb_client)
    
    # Mock get_full_list to return empty list to simulate new file
    mock_pb_client.collection.return_value.get_full_list.return_value = []

    result = run_discovery()

    assert result["status"] == "success"
    assert result["new_files"] == 1
    assert result["updated_files"] == 0
    assert len(result["errors"]) == 0

    # Verify PocketBase was called correctly for the new file insertion
    mock_pb_client.collection.assert_called_with('music_file')
    create_call = mock_pb_client.collection.return_value.create.call_args[0][0]
    assert create_call['source_dir'] == 'yubal'
    assert create_call['codec'] == 'flac'

def test_run_discovery_update_file(tmp_path, mocker):
    mocker.patch.object(settings, "ingest_base_path", str(tmp_path / "downloads" / "unseeded" / "music"))
    
    yubal_dir = tmp_path / "downloads" / "unseeded" / "music" / "yubal"
    yubal_dir.mkdir(parents=True)
    yubal_dir.joinpath("existing_song.flac").touch()

    filepath = str(yubal_dir.joinpath("existing_song.flac"))

    mocker.patch("src.services.discover.stat_fingerprint", return_value="12345:67890")
    mocker.patch("src.services.discover.extract_metadata", return_value={})
    
    mock_pb_client = mocker.MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb_client)
    
    # Mock existing record with a DIFFERENT hash via get_full_list
    existing_record = mocker.MagicMock(file_path=filepath, file_hash="old_hash", id="rec_123")
    mock_pb_client.collection.return_value.get_full_list.return_value = [existing_record]

    result = run_discovery()

    assert result["status"] == "success"
    assert result["new_files"] == 0
    assert result["updated_files"] == 1

    # Verify PocketBase was called correctly to update the fingerprint
    mock_pb_client.collection.return_value.update.assert_called_with("rec_123", {
        'file_hash': '12345:67890',
        'quality_score': None
    })


def test_run_discovery_metadata_timeout_skips_file(tmp_path, mocker):
    """If extract_metadata times out (stalled CIFS), the file is skipped and logged."""
    mocker.patch.object(settings, "ingest_base_path", str(tmp_path / "downloads" / "unseeded" / "music"))

    yubal_dir = tmp_path / "downloads" / "unseeded" / "music" / "yubal"
    yubal_dir.mkdir(parents=True)
    yubal_dir.joinpath("slow.flac").touch()

    mocker.patch("src.services.discover.stat_fingerprint", return_value="999:111")

    # Make extract_metadata time out
    mocker.patch(
        "src.services.discover.extract_metadata",
        side_effect=concurrent.futures.TimeoutError
    )

    mock_pb_client = mocker.MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb_client)
    mock_pb_client.collection.return_value.get_full_list.return_value = []

    result = run_discovery()

    # File is skipped, not counted as new, and the error is logged
    assert result["new_files"] == 0
    assert len(result["errors"]) == 1
    assert "Timed out" in result["errors"][0]
    # PocketBase create was never called
    mock_pb_client.collection.return_value.create.assert_not_called()


# ── extract_metadata ───────────────────────────────────────────────────────────

def _make_mutagen_mock(info_class_name, tags: dict):
    """Build a minimal mutagen.File-like mock with the given info class and tags."""
    f = MagicMock()
    f.info.__class__.__name__ = info_class_name
    # Make hasattr checks work
    f.info.sample_rate = 44100
    f.info.bitrate = 320000
    f.info.length = 240.0
    # tags dict — .get() must behave like a real dict
    f.tags = MagicMock()
    f.tags.__bool__ = lambda s: True
    f.tags.get.side_effect = lambda key, default=None: tags.get(key, default)
    return f


def test_extract_metadata_mp4_tags(tmp_path):
    """M4A files use ©nam/©ART/©alb keys — these must be read correctly."""
    dummy = tmp_path / "track.m4a"
    dummy.touch()

    mock_f = _make_mutagen_mock("MP4Info", {
        '\xa9nam': ['Lovely Bukhaar'],
        '\xa9ART': ['Ali Sethi'],
        '\xa9alb': ['Lovely Bukhaar (Dolby Atmos Version)'],
    })
    mock_f.__class__.__name__ = "MP4"

    with patch("src.services.discover.mutagen.File", return_value=mock_f):
        meta = extract_metadata(dummy)

    assert meta['title'] == 'Lovely Bukhaar'
    assert meta['artist'] == 'Ali Sethi'
    assert meta['album'] == 'Lovely Bukhaar (Dolby Atmos Version)'
    assert meta['codec'] == 'aac'


def test_extract_metadata_vorbis_tags(tmp_path):
    """FLAC/OGG files use lowercase Vorbis Comment keys."""
    dummy = tmp_path / "track.flac"
    dummy.touch()

    mock_f = _make_mutagen_mock("FLACInfo", {
        'title':  ['Pasoori'],
        'artist': ['Ali Sethi'],
        'album':  ['Coke Studio Season 14'],
    })
    mock_f.__class__.__name__ = "FLAC"
    mock_f.info.bits_per_sample = 16

    with patch("src.services.discover.mutagen.File", return_value=mock_f):
        meta = extract_metadata(dummy)

    assert meta['title'] == 'Pasoori'
    assert meta['artist'] == 'Ali Sethi'
    assert meta['album'] == 'Coke Studio Season 14'
    assert meta['codec'] == 'flac'
    assert meta['bit_depth'] == 16


def test_extract_metadata_id3_tags(tmp_path):
    """MP3 files use ID3 keys TIT2/TPE1/TALB."""
    dummy = tmp_path / "track.mp3"
    dummy.touch()

    # Real mutagen ID3 TextFrames return their text when str() is called.
    def make_id3_frame(value):
        frame = MagicMock()
        frame.__str__ = MagicMock(return_value=value)
        return frame

    mock_f = _make_mutagen_mock("MP3Info", {
        'TIT2': make_id3_frame('Dil'),
        'TPE1': make_id3_frame('Ali Sethi'),
        'TALB': make_id3_frame('Aatish'),
    })
    mock_f.__class__.__name__ = "MP3"

    with patch("src.services.discover.mutagen.File", return_value=mock_f):
        meta = extract_metadata(dummy)

    assert meta['title'] == 'Dil'
    assert meta['artist'] == 'Ali Sethi'
    assert meta['album'] == 'Aatish'
    assert meta['codec'] == 'mp3'


def test_extract_metadata_flac_uses_file_class_not_info_class(tmp_path):
    """Regression: codec detection must use type(f).__name__, not type(f.info).__name__.
    mutagen.FLAC has info class 'StreamInfo', not 'FLACInfo' — the old check
    always fell through, leaving codec=None and causing 'lossy' verdicts."""
    dummy = tmp_path / "track.flac"
    dummy.touch()

    mock_f = _make_mutagen_mock("StreamInfo", {})  # info class is StreamInfo
    mock_f.__class__.__name__ = "FLAC"             # but file class is FLAC
    mock_f.info.bits_per_sample = 24

    with patch("src.services.discover.mutagen.File", return_value=mock_f):
        meta = extract_metadata(dummy)

    assert meta['codec'] == 'flac', (
        "FLAC codec must be detected via the file-object class (FLAC), "
        "not the info class (StreamInfo)"
    )
    assert meta['bit_depth'] == 24


def test_extract_metadata_mp3_uses_file_class_not_info_class(tmp_path):
    """Same regression for MP3: info class is 'MPEGInfo', not 'MP3Info'."""
    dummy = tmp_path / "track.mp3"
    dummy.touch()

    mock_f = _make_mutagen_mock("MPEGInfo", {})
    mock_f.__class__.__name__ = "MP3"

    with patch("src.services.discover.mutagen.File", return_value=mock_f):
        meta = extract_metadata(dummy)

    assert meta['codec'] == 'mp3'


def test_extract_metadata_returns_empty_strings_when_no_tags(tmp_path):
    """Files with no tags at all return empty strings, not None or crash."""
    dummy = tmp_path / "untagged.opus"
    dummy.touch()

    mock_f = _make_mutagen_mock("OggOpusInfo", {})
    mock_f.__class__.__name__ = "OggOpus"
    mock_f.tags.__bool__ = lambda s: False  # simulate missing tags

    with patch("src.services.discover.mutagen.File", return_value=mock_f):
        meta = extract_metadata(dummy)

    assert meta['title'] is None
    assert meta['artist'] is None
    assert meta['album'] is None
    assert meta['codec'] == 'opus'


# ── repair_file_metadata ───────────────────────────────────────────────────────

def _pb_for_repair(mocker, records_with_empty_meta):
    """Returns a mock PocketBase client for repair_file_metadata tests."""
    mock_pb = MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb)
    mock_pb.collection.return_value.get_full_list.return_value = records_with_empty_meta
    return mock_pb


def test_repair_updates_records_with_empty_metadata(mocker, tmp_path):
    """Files with ' |  | ' get their tags re-extracted and the DB record updated."""
    audio = tmp_path / "track.m4a"
    audio.write_bytes(b"\x00" * 64)

    record = MagicMock()
    record.id = "file_mp4"
    record.file_path = str(audio)

    mock_pb = _pb_for_repair(mocker, [record])

    mocker.patch(
        "src.services.discover.extract_metadata",
        return_value={
            "title": "Lovely Bukhaar", "artist": "Ali Sethi",
            "album": "Lovely Bukhaar (Dolby Atmos Version)", "codec": "aac",
            "sample_rate": 44100, "bitrate": 96000,
            "bit_depth": None, "duration_seconds": 204.0,
        },
    )

    result = repair_file_metadata()

    assert result["repaired"] == 1
    assert result["errors"] == []
    update_call = mock_pb.collection.return_value.update.call_args
    assert update_call.args[0] == "file_mp4"
    assert "Lovely Bukhaar | Ali Sethi" in update_call.args[1][MusicFile.RAW_META]


def test_repair_skips_file_still_empty_after_extraction(mocker, tmp_path):
    """If re-extraction still returns empty tags, the record is not updated and
    an error is logged."""
    audio = tmp_path / "untagged.opus"
    audio.write_bytes(b"\x00" * 64)

    record = MagicMock()
    record.id = "file_opus"
    record.file_path = str(audio)

    mock_pb = _pb_for_repair(mocker, [record])
    mocker.patch(
        "src.services.discover.extract_metadata",
        return_value={"title": "", "artist": "", "album": "", "codec": "opus",
                      "sample_rate": 48000, "bitrate": 128000,
                      "bit_depth": None, "duration_seconds": 180.0},
    )

    result = repair_file_metadata()

    assert result["repaired"] == 0
    assert len(result["errors"]) == 1
    mock_pb.collection.return_value.update.assert_not_called()


def test_repair_skips_missing_files(mocker, tmp_path):
    """Records pointing to a non-existent path are skipped and logged."""
    record = MagicMock()
    record.id = "file_gone"
    record.file_path = str(tmp_path / "ghost.flac")  # does not exist

    mock_pb = _pb_for_repair(mocker, [record])

    result = repair_file_metadata()

    assert result["repaired"] == 0
    assert len(result["errors"]) == 1
    assert "not found" in result["errors"][0]
    mock_pb.collection.return_value.update.assert_not_called()


def test_repair_empty_database(mocker):
    """No files with empty metadata → nothing to do."""
    mock_pb = _pb_for_repair(mocker, [])

    result = repair_file_metadata()

    assert result["checked"] == 0
    assert result["repaired"] == 0
    assert result["errors"] == []
    mock_pb.collection.return_value.update.assert_not_called()
