import re
import logging
from pathlib import Path
from typing import Dict, Any

from src.core.config import settings
from src.core.schema import COLL_RELEASE, COLL_FILE, Release, MusicFile
from src.services.discover import get_pb_client

logger = logging.getLogger(__name__)

_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _sanitize(name: str) -> str:
    """Strip filesystem-unsafe chars; collapse whitespace."""
    cleaned = _UNSAFE.sub('_', name)
    return ' '.join(cleaned.split()).strip()


_CODEC_EXT = {'flac': '.flac', 'opus': '.opus', 'aac': '.m4a', 'mp3': '.mp3'}


def _target_path(release, file_record, library: Path) -> Path:
    """Compute the canonical symlink path for a primary file.

    Layout: {library}/{artist}/{album or 'Singles'}/{title}{ext}
    """
    artist = _sanitize(getattr(release, Release.ARTIST, '') or '') or 'Unknown Artist'
    title  = _sanitize(getattr(release, Release.TITLE,  '') or '') or 'Unknown Title'
    album  = _sanitize(getattr(release, Release.ALBUM,  '') or '')
    codec  = getattr(file_record, MusicFile.CODEC, '') or ''
    fpath  = getattr(file_record, MusicFile.FILE_PATH, '') or ''
    ext    = _CODEC_EXT.get(codec, Path(fpath).suffix)
    folder = album or 'Singles'
    return library / artist / folder / f"{title}{ext}"


def run_symlink() -> Dict[str, Any]:
    """Create/update symlinks for primary files; remove stale ones."""
    library = Path(settings.media_library_path)
    pb = get_pb_client()

    stats: Dict[str, Any] = {
        "status": "success",
        "created": 0,
        "updated": 0,
        "removed": 0,
        "plex_scan_triggered": False,
        "errors": [],
    }

    # 1. Load all releases into a lookup dict (single bulk query)
    all_releases = pb.collection(COLL_RELEASE).get_full_list()
    releases_by_id = {r.id: r for r in all_releases}

    # 2. Fetch all primary files
    primary_files = pb.collection(COLL_FILE).get_full_list(
        query_params={"filter": f"{MusicFile.IS_PRIMARY}=true"}
    )

    print(f"STATUS: Processing {len(primary_files)} primary files.")

    # 3. Process each primary file
    for file_record in primary_files:
        file_path_str = getattr(file_record, MusicFile.FILE_PATH, '') or ''
        file_id = file_record.id

        # a. Look up release
        release_id = getattr(file_record, MusicFile.RELEASE, None)
        if not release_id or release_id not in releases_by_id:
            msg = f"Primary file {file_id} has no valid release — skipping"
            logger.warning(msg)
            stats["errors"].append(msg)
            continue

        release = releases_by_id[release_id]

        # b. Check file exists on disk
        if not file_path_str or not Path(file_path_str).exists():
            msg = f"Primary file not found on disk: {file_path_str or file_id}"
            logger.warning(msg)
            stats["errors"].append(msg)
            continue

        # c. Compute expected symlink path
        expected = _target_path(release, file_record, library)

        # d. Current symlink path (stored in DB)
        current = getattr(file_record, MusicFile.SYMLINK_PATH, None) or None

        # e. If old symlink is at a different location, remove it
        if current and str(expected) != current:
            old_path = Path(current)
            if old_path.is_symlink():
                old_path.unlink()
                stats["removed"] += 1

        # f. If expected is already a valid symlink to the same source → no-op
        if (expected.is_symlink()
                and str(expected.resolve()) == str(Path(file_path_str).resolve())):
            continue

        # g. Create/replace symlink
        expected.parent.mkdir(parents=True, exist_ok=True)
        if expected.exists() or expected.is_symlink():
            expected.unlink()
        expected.symlink_to(file_path_str)

        # h. Update PocketBase
        pb.collection(COLL_FILE).update(file_id, {MusicFile.SYMLINK_PATH: str(expected)})

        # i. Track stats
        if current is None:
            stats["created"] += 1
        else:
            stats["updated"] += 1

        # j. Log
        print(f"STATUS: Symlinked: {expected.name} → {Path(file_path_str).name}")

    # 4. Clean stale symlinks on non-primary files
    stale_files = pb.collection(COLL_FILE).get_full_list(
        query_params={"filter": f"{MusicFile.IS_PRIMARY}=false && {MusicFile.SYMLINK_PATH}!=''"}
    )

    for file_record in stale_files:
        symlink_path_str = getattr(file_record, MusicFile.SYMLINK_PATH, None) or None
        if not symlink_path_str:
            continue
        stale_path = Path(symlink_path_str)
        if stale_path.is_symlink():
            stale_path.unlink()
            stats["removed"] += 1
        pb.collection(COLL_FILE).update(file_record.id, {MusicFile.SYMLINK_PATH: ''})
        print(f"STATUS: Removed stale symlink: {stale_path.name}")

    print(
        f"STATUS: Done. created={stats['created']} updated={stats['updated']} "
        f"removed={stats['removed']} errors={len(stats['errors'])}"
    )
    return stats
