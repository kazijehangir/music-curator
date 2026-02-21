"""Unit tests for src/services/analyze.py.

All tests mock acoustid, librosa, numpy, and PocketBase so no real audio
files or network access are required.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.services.analyze import (
    generate_acoustid,
    get_spectral_ceiling,
    calculate_quality_score,
    run_analysis,
)


# ── generate_acoustid ─────────────────────────────────────────────────────────

def test_generate_acoustid_success(tmp_path):
    """Happy path: acoustid.fingerprint_file returns (duration, bytes fingerprint)."""
    dummy_file = tmp_path / "track.flac"
    dummy_file.touch()

    with patch("src.services.analyze.acoustid.fingerprint_file", return_value=(180.0, b"abc123fp")):
        result = generate_acoustid(dummy_file)

    assert result == "abc123fp"


def test_generate_acoustid_returns_str_fingerprint(tmp_path):
    """If acoustid already returns a str fingerprint, it is passed through unchanged."""
    dummy_file = tmp_path / "track.opus"
    dummy_file.touch()

    with patch("src.services.analyze.acoustid.fingerprint_file", return_value=(200.0, "strfp999")):
        result = generate_acoustid(dummy_file)

    assert result == "strfp999"


def test_generate_acoustid_failure(tmp_path):
    """If acoustid raises, None is returned (no exception propagated)."""
    dummy_file = tmp_path / "broken.flac"
    dummy_file.touch()

    with patch("src.services.analyze.acoustid.fingerprint_file", side_effect=Exception("fpcalc not found")):
        result = generate_acoustid(dummy_file)

    assert result is None


# ── get_spectral_ceiling ──────────────────────────────────────────────────────

def test_get_spectral_ceiling_success(tmp_path):
    """Happy path: librosa returns a rolloff array and we return the mean."""
    import numpy as np

    dummy_file = tmp_path / "track.flac"
    dummy_file.touch()

    fake_audio = np.zeros(44100 * 15)
    fake_rolloff = np.array([[18000.0, 19000.0, 20000.0]])
    expected_mean = float(np.mean(fake_rolloff))

    with patch("src.services.analyze.librosa.load", return_value=(fake_audio, 44100)), \
         patch("src.services.analyze.librosa.feature.spectral_rolloff", return_value=fake_rolloff):
        result = get_spectral_ceiling(dummy_file)

    assert result == pytest.approx(expected_mean)


def test_get_spectral_ceiling_failure(tmp_path):
    """If librosa raises, None is returned (no exception propagated)."""
    dummy_file = tmp_path / "broken.opus"
    dummy_file.touch()

    with patch("src.services.analyze.librosa.load", side_effect=Exception("codec error")):
        result = get_spectral_ceiling(dummy_file)

    assert result is None


# ── calculate_quality_score ───────────────────────────────────────────────────

def test_quality_score_authentic_flac():
    """Genuine FLAC (spectral ceiling > 20 kHz) gets a high score and 'authentic' verdict."""
    score, verdict = calculate_quality_score(
        codec="flac", bitrate=1411000, bit_depth=16, spectral_ceiling=20500.0
    )
    assert score >= 80
    assert verdict == "authentic"


def test_quality_score_authentic_flac_24bit():
    """24-bit FLAC with full bandwidth earns the bonus points."""
    score, verdict = calculate_quality_score(
        codec="flac", bitrate=2822000, bit_depth=24, spectral_ceiling=21000.0
    )
    assert score >= 90
    assert verdict == "authentic"


def test_quality_score_fake_flac():
    """FLAC whose spectral ceiling barely reaches 15 kHz is penalised as 'fake'."""
    score, verdict = calculate_quality_score(
        codec="flac", bitrate=1411000, bit_depth=16, spectral_ceiling=14000.0
    )
    assert verdict == "fake"
    assert score < 50


def test_quality_score_suspicious_flac():
    """FLAC with ceiling between 16.5–19 kHz gets 'suspicious' and loses points."""
    score, verdict = calculate_quality_score(
        codec="flac", bitrate=1411000, bit_depth=16, spectral_ceiling=17500.0
    )
    assert verdict == "suspicious"


def test_quality_score_lossy_opus():
    """Opus is always labelled 'lossy' regardless of the spectral ceiling."""
    score, verdict = calculate_quality_score(
        codec="opus", bitrate=160000, bit_depth=None, spectral_ceiling=20000.0
    )
    assert verdict == "lossy"
    assert score >= 40


def test_quality_score_no_spectral_ceiling():
    """A missing spectral ceiling (None) still returns a sane score without crashing."""
    score, verdict = calculate_quality_score(
        codec="mp3", bitrate=320000, bit_depth=None, spectral_ceiling=None
    )
    assert 0 <= score <= 100
    assert verdict in {"authentic", "lossy", "fake", "suspicious", "warning"}


# ── run_analysis (integration-style, mocked PocketBase) ──────────────────────

def _make_pb_mock(mocker, unanalyzed_records, duplicate_files_items=None):
    """Helper: returns a configured mock PocketBase client.

    Both `PocketBase` and `settings` are imported *inside* `run_analysis`'s
    function body, so they don't exist as module-level attributes of analyze.py.
    We patch each at its canonical definition site instead.
    """
    mock_pb = MagicMock()
    # Patch the class at its canonical module so the local import in run_analysis picks it up
    mocker.patch("pocketbase.PocketBase", return_value=mock_pb)
    # Patch settings at its defined location (src.core.config)
    mocker.patch(
        "src.core.config.settings",
        pocketbase_url="http://localhost:8090",
        pocketbase_admin_email="admin@test.com",
        pocketbase_admin_password="testpass",
    )

    # get_full_list for unanalyzed files
    mock_pb.collection.return_value.get_full_list.return_value = unanalyzed_records

    # get_list for dedup fingerprint lookup
    dup_mock = MagicMock()
    dup_mock.items = duplicate_files_items or []
    mock_pb.collection.return_value.get_list.return_value = dup_mock

    return mock_pb


def test_run_analysis_new_release(mocker, tmp_path):
    """A new unique fingerprint creates a fresh music_release record."""
    audio_file = tmp_path / "new_track.flac"
    audio_file.write_bytes(b"\x00" * 1024)

    record = MagicMock()
    record.id = "file001"
    record.file_path = str(audio_file)
    record.codec = "flac"
    record.bitrate = 1411000
    record.bit_depth = 16
    record.raw_title__raw_artist__raw_album = "Pasoori | Ali Sethi | Coke Studio"

    mock_pb = _make_pb_mock(mocker, unanalyzed_records=[record])

    mocker.patch("src.services.analyze.generate_acoustid", return_value="fp_unique_001")
    mocker.patch("src.services.analyze.get_spectral_ceiling", return_value=20500.0)

    # Simulate no siblings yet after grouping
    mock_pb.collection.return_value.get_full_list.side_effect = [
        [record],          # 1st call: unanalyzed files
        [],                # 2nd call: siblings (empty — just created)
    ]

    new_release = MagicMock()
    new_release.id = "rel001"
    mock_pb.collection.return_value.create.return_value = new_release

    result = run_analysis()

    assert result["analyzed"] == 1
    assert result["new_releases"] == 1
    assert result["merged_files"] == 0
    assert result["errors"] == []


def test_run_analysis_fingerprint_dedup(mocker, tmp_path):
    """A duplicate fingerprint is merged into an existing release (not creating a new one)."""
    audio_file = tmp_path / "dupe_track.flac"
    audio_file.write_bytes(b"\x00" * 1024)

    record = MagicMock()
    record.id = "file002"
    record.file_path = str(audio_file)
    record.codec = "flac"
    record.bitrate = 1411000
    record.bit_depth = 16
    record.raw_title__raw_artist__raw_album = "Pasoori | Ali Sethi | Coke Studio"

    # An existing sibling with the same fingerprint, already in release "relExisting"
    existing_match = MagicMock()
    existing_match.release = "relExisting"

    mock_pb = _make_pb_mock(
        mocker,
        unanalyzed_records=[record],
        duplicate_files_items=[existing_match],
    )

    mocker.patch("src.services.analyze.generate_acoustid", return_value="fp_shared_001")
    mocker.patch("src.services.analyze.get_spectral_ceiling", return_value=20500.0)

    sibling = MagicMock()
    sibling.id = "file002"
    mock_pb.collection.return_value.get_full_list.side_effect = [
        [record],    # unanalyzed
        [sibling],   # siblings for best_file election
    ]

    result = run_analysis()

    assert result["analyzed"] == 1
    assert result["merged_files"] == 1
    assert result["new_releases"] == 0
    # create() should NOT have been called for music_release
    mock_pb.collection.return_value.create.assert_not_called()
