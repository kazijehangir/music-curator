import pytest
from unittest.mock import MagicMock
from pathlib import Path
from src.services.discover import run_discovery
from src.core.config import settings

def test_run_discovery_security_injection(tmp_path, mocker):
    """
    Test that filenames with backslashes and quotes are correctly escaped
    to prevent PocketBase filter injection.
    """
    # Setup ingest directory
    mocker.patch.object(settings, "ingest_base_path", str(tmp_path))
    ingest_dir = tmp_path / "downloads"
    ingest_dir.mkdir()

    # Create a file with a malicious name that includes both backslash and single quote.
    # Vulnerability: `replace("'", "\\'")` turns `\` into `\` and `'` into `\'`.
    # Result: `\\'` which might be interpreted as escaped backslash + unescaped quote.
    # We want: `\\\'` (escaped backslash + escaped quote).
    malicious_filename = "bad_file\\'.mp3"
    malicious_file = ingest_dir / malicious_filename
    malicious_file.touch()

    # Mock dependencies
    mocker.patch("src.services.discover.stat_fingerprint", return_value="hash123")
    mocker.patch("src.services.discover.extract_metadata", return_value={
        "codec": "mp3", "sample_rate": 44100, "bit_depth": 16,
        "bitrate": 128000, "duration_seconds": 100,
        "title": "Hack", "artist": "Hacker", "album": "Hacked"
    })

    mock_pb_client = mocker.MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb_client)

    # Mock get_list to return empty (file not found in DB) so it tries to create it
    mock_records = mocker.MagicMock()
    mock_records.items = []
    mock_pb_client.collection.return_value.get_list.return_value = mock_records

    # Run discovery
    run_discovery(pb=mock_pb_client, ingest_folders=["downloads"])

    # Check the filter string passed to get_list
    calls = mock_pb_client.collection.return_value.get_list.call_args_list
    assert len(calls) > 0

    filter_str = calls[0][0][2]["filter"]
    print(f"Filter string: {filter_str}")

    # We expect `bad_file` followed by `\` (escaped as `\\`) and `'` (escaped as `\'`).
    # Resulting substring should be: `bad_file\\\'`
    # (b,a,d,_,f,i,l,e,\, \, \, ')

    target_substring = r"bad_file\\\'"
    assert target_substring in filter_str, f"Filter string vulnerable! Got: {filter_str}"
