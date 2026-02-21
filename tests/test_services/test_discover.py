import pytest
import concurrent.futures
from pathlib import Path
from src.services.discover import run_discovery

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
    
    # Mock records.items to be empty to simulate new file
    mock_records = mocker.MagicMock()
    mock_records.items = []
    mock_pb_client.collection.return_value.get_list.return_value = mock_records

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

    mocker.patch("src.services.discover.stat_fingerprint", return_value="12345:67890")
    mocker.patch("src.services.discover.extract_metadata", return_value={})
    
    mock_pb_client = mocker.MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb_client)
    
    # Mock existing record with a DIFFERENT hash
    existing_record = mocker.MagicMock(file_hash="old_hash", id="rec_123")
    mock_records = mocker.MagicMock()
    mock_records.items = [existing_record]
    mock_pb_client.collection.return_value.get_list.return_value = mock_records

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
    mock_records = mocker.MagicMock()
    mock_records.items = []
    mock_pb_client.collection.return_value.get_list.return_value = mock_records

    result = run_discovery()

    # File is skipped, not counted as new, and the error is logged
    assert result["new_files"] == 0
    assert len(result["errors"]) == 1
    assert "Timed out" in result["errors"][0]
    # PocketBase create was never called
    mock_pb_client.collection.return_value.create.assert_not_called()
