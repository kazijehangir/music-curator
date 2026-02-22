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
    cleanup_orphaned_releases,
    reanalyze_quality,
)
from src.core.schema import COLL_RELEASE, COLL_FILE, MusicFile
import hashlib


# ── generate_acoustid ─────────────────────────────────────────────────────────

def test_generate_acoustid_success(tmp_path):
    """Happy path: acoustid.fingerprint_file returns (duration, bytes fingerprint)."""
    dummy_file = tmp_path / "track.flac"
    dummy_file.touch()

    expected = hashlib.sha256(b"abc123fp").hexdigest()[:16]

    # Mock mutagen to return None (trigger fallback)
    with patch("src.services.analyze.mutagen.File", return_value=None), \
         patch("src.services.analyze.acoustid.fingerprint_file", return_value=(180.0, b"abc123fp")):
        result = generate_acoustid(dummy_file)

    assert result == expected


def test_generate_acoustid_returns_str_fingerprint(tmp_path):
    """If acoustid already returns a str fingerprint, it is hashed and returned."""
    dummy_file = tmp_path / "track.opus"
    dummy_file.touch()

    expected = hashlib.sha256(b"strfp999").hexdigest()[:16]

    # Mock mutagen to return None (trigger fallback)
    with patch("src.services.analyze.mutagen.File", return_value=None), \
         patch("src.services.analyze.acoustid.fingerprint_file", return_value=(200.0, "strfp999")):
        result = generate_acoustid(dummy_file)

    assert result == expected


def test_generate_acoustid_from_metadata_flac(tmp_path):
    """Reads fingerprint from 'acoustid_fingerprint' tag (FLAC/beets)."""
    dummy_file = tmp_path / "meta.flac"
    dummy_file.touch()

    mock_mutagen = MagicMock()
    mock_mutagen.__contains__.side_effect = lambda k: k == 'acoustid_fingerprint'
    mock_mutagen.__getitem__.return_value = ["flac_meta_fp"]
    
    expected = hashlib.sha256(b"flac_meta_fp").hexdigest()[:16]

    with patch("src.services.analyze.mutagen.File", return_value=mock_mutagen):
        result = generate_acoustid(dummy_file)

    assert result == expected


def test_generate_acoustid_from_metadata_mp3(tmp_path):
    """Reads fingerprint from 'TXXX:Acoustid Fingerprint' tag (ID3)."""
    dummy_file = tmp_path / "meta.mp3"
    dummy_file.touch()

    mock_mutagen = MagicMock()
    mock_mutagen.__contains__.side_effect = lambda k: k == 'TXXX:Acoustid Fingerprint'
    mock_mutagen.__getitem__.return_value = ["mp3_meta_fp"]
    
    expected = hashlib.sha256(b"mp3_meta_fp").hexdigest()[:16]

    with patch("src.services.analyze.mutagen.File", return_value=mock_mutagen):
        result = generate_acoustid(dummy_file)

    assert result == expected


def test_generate_acoustid_failure(tmp_path):
    """If both metadata and acoustid raise, None is returned."""
    dummy_file = tmp_path / "broken.flac"
    dummy_file.touch()

    with patch("src.services.analyze.mutagen.File", side_effect=Exception("mutagen error")), \
         patch("src.services.analyze.acoustid.fingerprint_file", side_effect=Exception("fpcalc error")):
        result = generate_acoustid(dummy_file)

    assert result is None


# ── get_spectral_ceiling ──────────────────────────────────────────────────────

def test_get_spectral_ceiling_genuine_lossless(tmp_path):
    """Genuine lossless: highest bin above -60 dB is near Nyquist (~22 kHz)."""
    import numpy as np

    dummy_file = tmp_path / "track.flac"
    dummy_file.touch()

    sr = 44100
    fake_audio = np.zeros(sr * 15)
    # Simulate a magnitude spectrum where the bin at index 1020 (≈22 kHz) is
    # just above the -60 dB threshold and all higher bins are silent.
    n_bins = 1025  # n_fft=2048 → 1025 rfft bins
    fake_S = np.ones((n_bins, 10)) * 0.0001   # below threshold everywhere
    fake_S[1020, :] = 1.0                      # strong signal at ~22 kHz
    fake_freqs = np.linspace(0, sr / 2, n_bins)

    with patch("src.services.analyze.librosa.load", return_value=(fake_audio, sr)), \
         patch("src.services.analyze.librosa.stft", return_value=fake_S), \
         patch("src.services.analyze.librosa.fft_frequencies", return_value=fake_freqs):
        result = get_spectral_ceiling(dummy_file)

    assert result == pytest.approx(fake_freqs[1020])
    assert result > 20000  # well above any upscale cutoff


def test_get_spectral_ceiling_upscaled_flac(tmp_path):
    """Upscaled FLAC: all energy below 16 kHz, ceiling reflects the hard cutoff."""
    import numpy as np

    dummy_file = tmp_path / "upscale.flac"
    dummy_file.touch()

    sr = 44100
    fake_audio = np.zeros(sr * 15)
    n_bins = 1025
    # Energy only in bins 0-700 (~15 kHz), silence above
    fake_S = np.zeros((n_bins, 10))
    fake_S[:700, :] = 1.0
    fake_freqs = np.linspace(0, sr / 2, n_bins)

    with patch("src.services.analyze.librosa.load", return_value=(fake_audio, sr)), \
         patch("src.services.analyze.librosa.stft", return_value=fake_S), \
         patch("src.services.analyze.librosa.fft_frequencies", return_value=fake_freqs):
        result = get_spectral_ceiling(dummy_file)

    assert result == pytest.approx(fake_freqs[699])
    assert result < 16000  # hard cutoff → fake verdict territory


def test_get_spectral_ceiling_silent_file(tmp_path):
    """A completely silent file returns 0.0 instead of raising."""
    import numpy as np

    dummy_file = tmp_path / "silent.flac"
    dummy_file.touch()

    sr = 44100
    n_bins = 1025
    fake_S = np.zeros((n_bins, 10))
    fake_freqs = np.linspace(0, sr / 2, n_bins)

    with patch("src.services.analyze.librosa.load", return_value=(np.zeros(sr * 15), sr)), \
         patch("src.services.analyze.librosa.stft", return_value=fake_S), \
         patch("src.services.analyze.librosa.fft_frequencies", return_value=fake_freqs):
        result = get_spectral_ceiling(dummy_file)

    assert result == 0.0


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
    """FLAC with ceiling between 15.5-16.5 kHz gets 'suspicious' and loses points."""
    score, verdict = calculate_quality_score(
        codec="flac", bitrate=1411000, bit_depth=16, spectral_ceiling=16000.0
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
    record.release = None  # New file — no release yet

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
    record.release = None  # New file — no release yet

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


# ── run_analysis regression tests ─────────────────────────────────────────────

def test_run_analysis_no_duplicate_release_for_already_assigned_file(mocker, tmp_path):
    """Regression (Bug 2): a file that already has a release must NOT create a new
    release on re-analysis, even when no fingerprint duplicate is found in the DB."""
    audio_file = tmp_path / "already_grouped.flac"
    audio_file.write_bytes(b"\x00" * 1024)

    record = MagicMock()
    record.id = "file004"
    record.file_path = str(audio_file)
    record.codec = "flac"
    record.bitrate = 1411000
    record.bit_depth = 16
    record.raw_title__raw_artist__raw_album = "Song | Artist | Album"
    record.release = "existing_rel_abc"  # Already assigned from a prior run

    mock_pb = _make_pb_mock(mocker, unanalyzed_records=[record])

    mocker.patch("src.services.analyze.generate_acoustid", return_value="fp_unique_xyz")
    mocker.patch("src.services.analyze.get_spectral_ceiling", return_value=20000.0)

    sibling = MagicMock()
    sibling.id = "file004"
    mock_pb.collection.return_value.get_full_list.side_effect = [
        [record],    # unanalyzed files
        [sibling],   # siblings for best_file election
    ]

    result = run_analysis()

    assert result["new_releases"] == 0
    mock_pb.collection.return_value.create.assert_not_called()


def test_run_analysis_filter_excludes_broken_regex_operator(mocker):
    """Regression (Bug 1): the PocketBase query filter must not use the !~ operator.
    In PocketBase !~ means 'does not contain' (substring), not 'regex not-match',
    so `acoustid_fp!~'^[a-f0-9]{16}$'` matched every record and caused all files
    to be re-processed on every pipeline run."""
    mock_pb = _make_pb_mock(mocker, unanalyzed_records=[])

    run_analysis()

    call_kwargs = mock_pb.collection.return_value.get_full_list.call_args
    filter_str = call_kwargs.kwargs.get("query_params", {}).get("filter", "")
    assert "!~" not in filter_str, (
        "Filter must not use !~ (PocketBase substring-not-contains), "
        "which would match every file and cause repeated re-analysis"
    )


# ── cleanup_orphaned_releases ──────────────────────────────────────────────────

def _pb_for_cleanup(mocker, all_release_ids, referenced_release_ids):
    """Returns (mock_pb, release_coll_mock, file_coll_mock) configured for cleanup tests.

    all_release_ids: every release ID currently in music_release.
    referenced_release_ids: IDs that appear in at least one music_file.release field.
    """
    mock_pb = MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb)

    release_coll = MagicMock()
    file_coll = MagicMock()

    def _collection(name):
        return release_coll if name == COLL_RELEASE else file_coll

    mock_pb.collection.side_effect = _collection

    release_records = []
    for rid in all_release_ids:
        r = MagicMock()
        r.id = rid
        release_records.append(r)
    release_coll.get_full_list.return_value = release_records

    file_records = []
    for rid in referenced_release_ids:
        f = MagicMock()
        f.release = rid
        file_records.append(f)
    file_coll.get_full_list.return_value = file_records

    return mock_pb, release_coll, file_coll


def test_cleanup_deletes_orphaned_releases(mocker):
    """Releases not referenced by any file are deleted; referenced ones are kept."""
    _, release_coll, _ = _pb_for_cleanup(
        mocker,
        all_release_ids=["rel1", "rel2", "rel3"],
        referenced_release_ids=["rel1"],
    )

    result = cleanup_orphaned_releases()

    assert result["checked"] == 3
    assert result["deleted"] == 2
    assert result["errors"] == []
    deleted_ids = {call.args[0] for call in release_coll.delete.call_args_list}
    assert deleted_ids == {"rel2", "rel3"}


def test_cleanup_preserves_all_referenced_releases(mocker):
    """If every release has at least one file pointing to it, nothing is deleted."""
    _, release_coll, _ = _pb_for_cleanup(
        mocker,
        all_release_ids=["rel1", "rel2"],
        referenced_release_ids=["rel1", "rel2"],
    )

    result = cleanup_orphaned_releases()

    assert result["deleted"] == 0
    release_coll.delete.assert_not_called()


def test_cleanup_all_orphaned(mocker):
    """If no files exist at all, every release is deleted."""
    _, release_coll, _ = _pb_for_cleanup(
        mocker,
        all_release_ids=["rel1", "rel2", "rel3"],
        referenced_release_ids=[],
    )

    result = cleanup_orphaned_releases()

    assert result["deleted"] == 3
    assert result["errors"] == []


def test_cleanup_empty_database(mocker):
    """Empty database: nothing to check, nothing to delete, no errors."""
    _, release_coll, _ = _pb_for_cleanup(
        mocker,
        all_release_ids=[],
        referenced_release_ids=[],
    )

    result = cleanup_orphaned_releases()

    assert result["checked"] == 0
    assert result["deleted"] == 0
    assert result["errors"] == []
    release_coll.delete.assert_not_called()


def test_cleanup_handles_delete_error(mocker):
    """A failing delete is recorded in errors but does not abort remaining deletions."""
    _, release_coll, _ = _pb_for_cleanup(
        mocker,
        all_release_ids=["rel1", "rel2"],
        referenced_release_ids=[],
    )
    # First delete raises; second succeeds
    release_coll.delete.side_effect = [Exception("403 Forbidden"), None]

    result = cleanup_orphaned_releases()

    assert result["deleted"] == 1
    assert len(result["errors"]) == 1
    assert "rel1" in result["errors"][0]


# ── reanalyze_quality ──────────────────────────────────────────────────────────

def test_reanalyze_quality_updates_codec_and_verdict(mocker, tmp_path):
    """Re-scoring corrects stale quality fields — specifically codec=None that
    caused 'lossy' verdicts for all FLAC files (broken class-name detection)."""
    audio = tmp_path / "track.flac"
    audio.write_bytes(b"\x00" * 64)

    record = MagicMock()
    record.id = "file_flac"
    record.file_path = str(audio)

    mock_pb = MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb)
    mock_pb.collection.return_value.get_full_list.return_value = [record]

    mocker.patch(
        "src.services.discover.extract_metadata",
        return_value={"codec": "flac", "bit_depth": 24, "bitrate": 3000000,
                      "title": "Pasoori", "artist": "Ali Sethi", "album": "CS14",
                      "sample_rate": 96000, "duration_seconds": 240.0},
    )
    mocker.patch("src.services.analyze.get_spectral_ceiling", return_value=26500.0)

    result = reanalyze_quality()

    assert result["processed"] == 1
    assert result["errors"] == []

    update_call = mock_pb.collection.return_value.update.call_args
    updated_fields = update_call.args[1]
    assert updated_fields[MusicFile.CODEC] == "flac"
    assert updated_fields[MusicFile.QUALITY_VERDICT] == "authentic"
    assert updated_fields[MusicFile.QUALITY_SCORE] == 100


def test_reanalyze_quality_skips_missing_files(mocker, tmp_path):
    """Files that no longer exist on disk are skipped and logged."""
    record = MagicMock()
    record.id = "file_gone"
    record.file_path = str(tmp_path / "ghost.flac")

    mock_pb = MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb)
    mock_pb.collection.return_value.get_full_list.return_value = [record]

    result = reanalyze_quality()

    assert result["processed"] == 0
    assert len(result["errors"]) == 1
    mock_pb.collection.return_value.update.assert_not_called()


def test_reanalyze_quality_empty_database(mocker):
    """Empty database: nothing to process, no errors."""
    mock_pb = MagicMock()
    mocker.patch("src.services.discover.get_pb_client", return_value=mock_pb)
    mock_pb.collection.return_value.get_full_list.return_value = []

    result = reanalyze_quality()

    assert result["processed"] == 0
    assert result["errors"] == []
    mock_pb.collection.return_value.update.assert_not_called()
