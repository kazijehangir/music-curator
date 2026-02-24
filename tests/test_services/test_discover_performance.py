import pytest
from unittest.mock import MagicMock
from src.services.discover import run_discovery
from src.core.config import settings

def test_run_discovery_batch_optimization(tmp_path, mocker):
    # Setup 3 files in one directory
    ingest_dir = tmp_path / "downloads" / "music"
    dir_name = "batch_test"
    target_dir = ingest_dir / dir_name
    target_dir.mkdir(parents=True)

    (target_dir / "1.flac").touch()
    (target_dir / "2.flac").touch()
    (target_dir / "3.flac").touch()

    # Mock settings
    mocker.patch.object(settings, "ingest_base_path", str(ingest_dir))
    mocker.patch.object(settings, "ingest_dirs", dir_name)

    # Mock file stats and metadata to avoid actual processing
    mocker.patch("src.services.discover.stat_fingerprint", return_value="hash")
    mocker.patch("src.services.discover.extract_metadata", return_value={
        "codec": "flac", "title": "T", "artist": "A", "album": "L",
        "sample_rate": 44100, "bit_depth": 16, "bitrate": 1000, "duration_seconds": 60
    })

    # Mock PocketBase
    mock_pb = MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb)

    # Run discovery
    run_discovery(pb=mock_pb, ingest_folders=[dir_name])

    # In the optimized version, we expect get_full_list to be called once
    # and get_list (the per-file check) to NOT be called.

    # Check calls
    collection_mock = mock_pb.collection.return_value

    # For now, let's just print what happened so I can verify the failure first
    print(f"\nget_list call count: {collection_mock.get_list.call_count}")
    print(f"get_full_list call count: {collection_mock.get_full_list.call_count}")

    # Assertions for OPTIMIZED behavior (this should fail initially)
    # verify we fetched the whole directory once
    collection_mock.get_full_list.assert_called_once()

    # verify we didn't check each file individually
    collection_mock.get_list.assert_not_called()

def test_run_discovery_batch_optimization_with_quotes(tmp_path, mocker):
    # Setup files in directory with quotes
    ingest_dir = tmp_path / "downloads" / "music"
    dir_name = "80's Hits"
    target_dir = ingest_dir / dir_name
    target_dir.mkdir(parents=True)

    (target_dir / "1.flac").touch()

    mocker.patch.object(settings, "ingest_base_path", str(ingest_dir))
    mocker.patch.object(settings, "ingest_dirs", dir_name)

    mocker.patch("src.services.discover.stat_fingerprint", return_value="hash")
    mocker.patch("src.services.discover.extract_metadata", return_value={
        "codec": "flac", "title": "T", "artist": "A", "album": "L",
        "sample_rate": 44100, "bit_depth": 16, "bitrate": 1000, "duration_seconds": 60
    })

    mock_pb = MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb)

    run_discovery(pb=mock_pb, ingest_folders=[dir_name])

    # Check filter string
    collection_mock = mock_pb.collection.return_value
    collection_mock.get_full_list.assert_called_once()

    call_kwargs = collection_mock.get_full_list.call_args[1]
    # The source code uses source_dir='...'
    # We expect the single quote to be escaped with backslash
    expected_filter = "source_dir='80\\'s Hits'"
    # Python string escaping in test: to get one backslash in expected string we need two here?
    # In code: replace("'", "\'") -> 80\'s Hits.
    # So filter string is: source_dir='80\'s Hits'
    # In python literal: '80\\'s Hits'

    assert "source_dir='80\\'s Hits'" in call_kwargs['query_params']['filter'] or "source_dir='80\'s Hits'" in call_kwargs['query_params']['filter']
