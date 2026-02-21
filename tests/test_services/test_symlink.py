"""Unit tests for src/services/symlink.py.

All tests mock PocketBase and settings so no real database or network
access are required. Real filesystem calls (mkdir, symlink_to, unlink)
use pytest's tmp_path fixture — pyfakefs is intentionally avoided because
symlinks need real kernel support.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, call

from src.services.symlink import _sanitize, _target_path, run_symlink
from src.core.schema import COLL_RELEASE, COLL_FILE, MusicFile


# ── _sanitize ─────────────────────────────────────────────────────────────────

def test_sanitize_strips_unsafe_chars():
    """: / ? and other unsafe chars are replaced with _; whitespace collapsed."""
    result = _sanitize('Artist: Name/Sub?Dir')
    assert ':' not in result
    assert '/' not in result
    assert '?' not in result
    assert result == 'Artist_ Name_Sub_Dir'


def test_sanitize_collapses_whitespace():
    """Multiple spaces and surrounding whitespace are collapsed."""
    result = _sanitize('  Track   Title  ')
    assert result == 'Track Title'


def test_sanitize_empty_string():
    """Empty string returns empty string; caller is responsible for fallback."""
    assert _sanitize('') == ''


# ── _target_path ──────────────────────────────────────────────────────────────

def _make_release(title='Track', artist='Artist', album='Album'):
    r = MagicMock()
    r.title = title
    r.artist = artist
    r.album = album
    return r


def _make_file_record(codec='flac', file_path='/music/track.flac'):
    f = MagicMock()
    f.codec = codec
    f.file_path = file_path
    return f


def test_target_path_with_album(tmp_path):
    """Layout: library/Artist/Album/Title.flac"""
    library = tmp_path / 'library'
    release = _make_release(title='Pasoori', artist='Ali Sethi', album='Coke Studio 14')
    file_rec = _make_file_record(codec='flac', file_path='/music/pasoori.flac')

    result = _target_path(release, file_rec, library)

    assert result == library / 'Ali Sethi' / 'Coke Studio 14' / 'Pasoori.flac'


def test_target_path_singles(tmp_path):
    """Empty album → folder is 'Singles'."""
    library = tmp_path / 'library'
    release = _make_release(title='Rung', artist='Farida Khanum', album='')
    file_rec = _make_file_record(codec='flac', file_path='/music/rung.flac')

    result = _target_path(release, file_rec, library)

    assert result == library / 'Farida Khanum' / 'Singles' / 'Rung.flac'


def test_target_path_codec_ext_mapping(tmp_path):
    """Codec → extension: flac→.flac, opus→.opus, aac→.m4a, mp3→.mp3."""
    library = tmp_path / 'library'
    release = _make_release(title='Song', artist='X', album='Y')

    cases = [
        ('flac', '.flac'),
        ('opus', '.opus'),
        ('aac',  '.m4a'),
        ('mp3',  '.mp3'),
    ]
    for codec, expected_ext in cases:
        file_rec = _make_file_record(codec=codec, file_path=f'/music/song.{codec}')
        result = _target_path(release, file_rec, library)
        assert result.suffix == expected_ext, f"codec={codec!r} should map to {expected_ext!r}"


def test_target_path_unknown_codec_falls_back_to_file_ext(tmp_path):
    """Unknown codec falls back to the actual file extension."""
    library = tmp_path / 'library'
    release = _make_release(title='Song', artist='X', album='Y')
    file_rec = _make_file_record(codec='wav', file_path='/music/song.wav')

    result = _target_path(release, file_rec, library)

    assert result.suffix == '.wav'


# ── run_symlink helpers ────────────────────────────────────────────────────────

def _make_pb_mock(mocker, releases, primary_files, stale_files=None, library_path='/fake/library'):
    """Returns a configured mock PocketBase client.

    get_full_list side_effect order mirrors run_symlink() call order:
      1. all releases (COLL_RELEASE)
      2. is_primary=true files (COLL_FILE)
      3. is_primary=false && symlink_path!='' files (COLL_FILE)
    """
    mock_pb = MagicMock()
    mocker.patch("src.services.symlink.get_pb_client", return_value=mock_pb)
    mocker.patch(
        "src.services.symlink.settings",
        media_library_path=library_path,
    )

    mock_pb.collection.return_value.get_full_list.side_effect = [
        releases,
        primary_files,
        stale_files if stale_files is not None else [],
    ]
    return mock_pb


def _primary_file(file_path, release_id, codec='flac', symlink_path=None, file_id='file001'):
    rec = MagicMock()
    rec.id = file_id
    rec.file_path = file_path
    rec.release = release_id
    rec.codec = codec
    rec.symlink_path = symlink_path
    rec.is_primary = True
    return rec


def _release(title='Track', artist='Artist', album='Album', release_id='rel001'):
    r = MagicMock()
    r.id = release_id
    r.title = title
    r.artist = artist
    r.album = album
    return r


# ── run_symlink unit tests ─────────────────────────────────────────────────────

def test_run_symlink_creates_new(mocker, tmp_path):
    """Primary file with no existing symlink → symlink created, created++."""
    audio = tmp_path / 'track.flac'
    audio.write_bytes(b'\x00' * 64)
    library = tmp_path / 'library'

    release = _release(title='Pasoori', artist='Ali Sethi', album='Coke Studio')
    file_rec = _primary_file(str(audio), 'rel001', codec='flac', symlink_path=None)

    mock_pb = _make_pb_mock(mocker, [release], [file_rec], [], str(library))

    result = run_symlink()

    assert result['created'] == 1
    assert result['updated'] == 0
    assert result['removed'] == 0
    assert result['errors'] == []
    assert result['plex_scan_triggered'] is False

    expected_link = library / 'Ali Sethi' / 'Coke Studio' / 'Pasoori.flac'
    assert expected_link.is_symlink()
    assert expected_link.resolve() == audio.resolve()

    mock_pb.collection.return_value.update.assert_called_once_with(
        'file001', {MusicFile.SYMLINK_PATH: str(expected_link)}
    )


def test_run_symlink_skips_correct_existing(mocker, tmp_path):
    """Valid symlink already at the correct path → no-op, update() not called."""
    audio = tmp_path / 'track.flac'
    audio.write_bytes(b'\x00' * 64)
    library = tmp_path / 'library'

    # Pre-create the exact symlink that run_symlink() would compute
    expected_link = library / 'Ali Sethi' / 'Coke Studio' / 'Pasoori.flac'
    expected_link.parent.mkdir(parents=True)
    expected_link.symlink_to(str(audio))

    release = _release(title='Pasoori', artist='Ali Sethi', album='Coke Studio')
    file_rec = _primary_file(
        str(audio), 'rel001', codec='flac', symlink_path=str(expected_link)
    )

    mock_pb = _make_pb_mock(mocker, [release], [file_rec], [], str(library))

    result = run_symlink()

    assert result['created'] == 0
    assert result['updated'] == 0
    assert result['removed'] == 0
    assert result['errors'] == []
    mock_pb.collection.return_value.update.assert_not_called()


def test_run_symlink_updates_moved_path(mocker, tmp_path):
    """Release metadata changed → old symlink removed, new one created, updated++."""
    audio = tmp_path / 'track.flac'
    audio.write_bytes(b'\x00' * 64)
    library = tmp_path / 'library'

    # Old symlink at the previous (now stale) location
    old_link = library / 'Old Artist' / 'Singles' / 'Pasoori.flac'
    old_link.parent.mkdir(parents=True)
    old_link.symlink_to(str(audio))

    # Release now has updated artist name → different target path
    release = _release(title='Pasoori', artist='Ali Sethi', album='Coke Studio')
    file_rec = _primary_file(
        str(audio), 'rel001', codec='flac', symlink_path=str(old_link)
    )

    mock_pb = _make_pb_mock(mocker, [release], [file_rec], [], str(library))

    result = run_symlink()

    assert result['updated'] == 1
    assert result['removed'] == 1
    assert result['created'] == 0
    assert result['errors'] == []

    # Old symlink gone, new one present
    assert not old_link.exists()
    new_link = library / 'Ali Sethi' / 'Coke Studio' / 'Pasoori.flac'
    assert new_link.is_symlink()
    assert new_link.resolve() == audio.resolve()


def test_run_symlink_cleans_stale(mocker, tmp_path):
    """Non-primary file with symlink_path set → symlink removed, field cleared."""
    audio = tmp_path / 'track.flac'
    audio.write_bytes(b'\x00' * 64)
    library = tmp_path / 'library'

    # Create a stale symlink on disk
    stale_link = library / 'Stale' / 'Singles' / 'OldTrack.flac'
    stale_link.parent.mkdir(parents=True)
    stale_link.symlink_to(str(audio))

    stale_rec = MagicMock()
    stale_rec.id = 'file_stale'
    stale_rec.symlink_path = str(stale_link)
    stale_rec.is_primary = False

    mock_pb = _make_pb_mock(mocker, [], [], [stale_rec], str(library))

    result = run_symlink()

    assert result['removed'] == 1
    assert result['created'] == 0
    assert result['updated'] == 0
    assert result['errors'] == []

    # Symlink gone from disk
    assert not stale_link.exists()

    # PocketBase field cleared
    mock_pb.collection.return_value.update.assert_called_once_with(
        'file_stale', {MusicFile.SYMLINK_PATH: ''}
    )


def test_run_symlink_skips_missing_file(mocker, tmp_path):
    """file_path not on disk → error logged, no symlink created."""
    library = tmp_path / 'library'
    ghost_path = str(tmp_path / 'ghost.flac')  # does not exist

    release = _release()
    file_rec = _primary_file(ghost_path, 'rel001', codec='flac')

    mock_pb = _make_pb_mock(mocker, [release], [file_rec], [], str(library))

    result = run_symlink()

    assert result['created'] == 0
    assert len(result['errors']) == 1
    assert 'ghost.flac' in result['errors'][0]
    mock_pb.collection.return_value.update.assert_not_called()


def test_run_symlink_skips_missing_release(mocker, tmp_path):
    """file.release ID not in DB → error logged, no symlink created."""
    audio = tmp_path / 'track.flac'
    audio.write_bytes(b'\x00' * 64)
    library = tmp_path / 'library'

    file_rec = _primary_file(str(audio), 'nonexistent_rel_id', codec='flac')

    # No releases in DB
    mock_pb = _make_pb_mock(mocker, [], [file_rec], [], str(library))

    result = run_symlink()

    assert result['created'] == 0
    assert len(result['errors']) == 1
    assert 'file001' in result['errors'][0]
    mock_pb.collection.return_value.update.assert_not_called()


def test_run_symlink_empty_database(mocker, tmp_path):
    """No primary files → all counters zero, no crash."""
    library = tmp_path / 'library'
    mock_pb = _make_pb_mock(mocker, [], [], [], str(library))

    result = run_symlink()

    assert result['created'] == 0
    assert result['updated'] == 0
    assert result['removed'] == 0
    assert result['errors'] == []
    assert result['plex_scan_triggered'] is False
    mock_pb.collection.return_value.update.assert_not_called()
