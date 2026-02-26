import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.services.discover import run_discovery
from src.core.config import settings

def test_run_discovery_security_injection(tmp_path, mocker):
    """
    Security Test: Ensure filenames with special characters (backslashes + quotes)
    are correctly escaped to prevent filter injection.

    Vulnerability:
    If a file is named "foo\'bar.mp3", simply replacing "'" with "\'" results in:
    "foo\\'bar.mp3".
    PocketBase interprets this as:
    - 'foo' (literal)
    - \' (escaped backslash -> literal backslash)
    - ' (end of string)
    - bar.mp3 (extra SQL/filter syntax -> INJECTION or ERROR)

    Correct escaping should be: "foo\\\'bar.mp3".
    - 'foo' (literal)
    - \\ (escaped backslash -> literal backslash)
    - \' (escaped quote -> literal quote)
    - ' (end of string)
    """
    # 1. Setup simulated environment
    # Create a directory structure
    music_dir = tmp_path / "downloads" / "music"
    music_dir.mkdir(parents=True)

    # Create a file with a dangerous name: foo\'bar.mp3
    # Note: On Linux, backslash is a valid character.
    dangerous_filename = "foo\\'bar.mp3"
    dangerous_file = music_dir / dangerous_filename
    dangerous_file.touch()

    # Mock settings
    mocker.patch.object(settings, "ingest_base_path", str(tmp_path / "downloads"))
    mocker.patch.object(settings, "ingest_dirs", "music")

    # Mock dependencies to avoid side effects
    mocker.patch("src.services.discover.stat_fingerprint", return_value="hash123")
    # Mock extract_metadata to return dummy data
    mocker.patch("src.services.discover.extract_metadata", return_value={
        "codec": "mp3",
        "sample_rate": 44100,
        "bit_depth": 16,
        "bitrate": 320000,
        "duration_seconds": 120,
        "title": "Safe Title",
        "artist": "Safe Artist",
        "album": "Safe Album"
    })

    # Mock PocketBase client
    mock_pb_client = MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb_client)

    # Mock get_list return value (empty -> treat as new file)
    mock_records = MagicMock()
    mock_records.items = []
    mock_pb_client.collection.return_value.get_list.return_value = mock_records

    # 2. Run discovery
    run_discovery()

    # 3. Assertions
    # We want to check the filter passed to get_list
    # The file path is absolute: /tmp/.../downloads/music/foo\'bar.mp3
    expected_path_str = str(dangerous_file)

    # Calculate the INCORRECT escaped string (what the current code does)
    # It replaces ' with \'
    incorrectly_escaped = expected_path_str.replace("'", "\\'")

    # Calculate the CORRECT escaped string (what we WANT)
    # It replaces \ with \\ AND ' with \'
    correctly_escaped = expected_path_str.replace('\\', '\\\\').replace("'", "\\'")

    # Verify that the correct escaping is DIFFERENT from incorrect escaping
    # (This confirms our test case is valid for reproducing the issue)
    assert correctly_escaped != incorrectly_escaped, "Test case invalid: expected and incorrect escaping are identical"

    # Check what was actually called
    # We expect this assertion to FAIL if the vulnerability exists
    calls = mock_pb_client.collection.return_value.get_list.call_args_list
    assert len(calls) > 0, "get_list should have been called"

    # Find the call for our file
    # The filter arg is index 2 (or kwargs 'filter')
    # call_args is (args, kwargs)
    # args: (page, per_page, query_params)

    actual_call_args = calls[0][0] # tuple of args
    # Verify it is called with 3 args: 1, 1, query_params
    assert len(actual_call_args) >= 3
    query_params = actual_call_args[2]
    actual_filter = query_params.get("filter", "")

    expected_filter = f"file_path='{correctly_escaped}'"

    print(f"\nExpected filter: {expected_filter}")
    print(f"Actual filter:   {actual_filter}")

    assert actual_filter == expected_filter, f"Vulnerability detected! Filter was not properly escaped.\nExpected: {expected_filter}\nActual:   {actual_filter}"
