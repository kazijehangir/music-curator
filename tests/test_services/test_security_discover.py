import pytest
from unittest.mock import MagicMock, call
from src.services.discover import run_discovery
from src.core.config import settings

def test_run_discovery_prevents_injection(tmp_path, mocker):
    """
    Regression Test:
    Ensures that filenames containing backslashes and single quotes are correctly escaped
    to prevent PocketBase filter injection.

    Vulnerability Scenario:
    If a filename is "fake\'injection.mp3", a naive replace("'", "\\'") results in "fake\\'injection.mp3".
    In a filter 'file_path='...', this becomes 'file_path='fake\\'injection.mp3''.
    The first backslash escapes the second, leaving the quote unescaped.

    Correct Behavior:
    The backslash should be escaped first: "fake\\'injection.mp3" -> "fake\\\\'injection.mp3".
    Filter becomes 'file_path='fake\\\\'injection.mp3'', which is interpreted as literal backslash + escaped quote.
    """
    # Setup mock file system
    mocker.patch.object(settings, "ingest_base_path", str(tmp_path))
    ingest_dir = tmp_path / "music"
    ingest_dir.mkdir()

    # Create a file with a problematic name: "fake\'injection.mp3"
    bad_filename = "fake\\'injection.mp3"
    (ingest_dir / bad_filename).touch()

    # Mock dependencies
    mocker.patch("src.services.discover.stat_fingerprint", return_value="hash123")
    mocker.patch("src.services.discover.extract_metadata", return_value={
        "codec": "mp3", "sample_rate": 44100, "bit_depth": 16,
        "bitrate": 320000, "duration_seconds": 180,
        "title": "T", "artist": "A", "album": "B"
    })

    mock_pb_client = mocker.MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb_client)

    # Mock get_list to return empty items (simulating new file)
    mock_records = mocker.MagicMock()
    mock_records.items = []
    mock_pb_client.collection.return_value.get_list.return_value = mock_records

    # Run discovery
    run_discovery(ingest_folders=["music"])

    # Check the filter string passed to get_list
    # expected_good_filter: "file_path='.../fake\\\\'injection.mp3'" (secure, 3 backslashes + quote in literal)

    calls = mock_pb_client.collection.return_value.get_list.call_args_list
    assert len(calls) > 0

    args, kwargs = calls[0]
    if len(args) >= 3:
        filter_str = args[2]['filter']
    else:
        filter_str = kwargs.get('query_params', {}).get('filter')

    # We expect 3 backslashes followed by a quote (escaped backslash + escaped quote)
    # Python literal for 3 backslashes is "\\\\\\"
    assert "fake\\\\\\'injection.mp3" in filter_str, \
        f"Filter is vulnerable! Expected 3 backslashes escaping, found: {filter_str}"
