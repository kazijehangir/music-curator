import os
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, Optional
import mutagen
from pocketbase import PocketBase

from src.core.config import settings

# Seconds to allow for mutagen metadata extraction per file before giving up.
# Applies as a safety net — stat_fingerprint itself is near-instant.
FILE_TIMEOUT_SECONDS = 30


def get_pb_client() -> PocketBase:
    client = PocketBase(settings.pocketbase_url)
    client.admins.auth_with_password(
        settings.pocketbase_admin_email,
        settings.pocketbase_admin_password
    )
    return client


def stat_fingerprint(filepath: Path) -> str:
    """
    Returns a lightweight change-detection fingerprint using only os.stat().

    Uses (file size, mtime_ns) — a single syscall with zero file reads.
    This avoids reading FLAC data over CIFS, which was causing kernel D-state hangs.
    Sufficient for detecting file changes; SHA-256 is unnecessary for this purpose.
    """
    s = filepath.stat()
    return f"{s.st_size}:{s.st_mtime_ns}"

def extract_metadata(filepath: Path) -> Dict[str, Any]:
    """Extract audio metadata using mutagen."""
    meta = {
        "codec": None,
        "sample_rate": None,
        "bit_depth": None,
        "bitrate": None,
        "duration_seconds": None,
        "title": None,
        "artist": None,
        "album": None
    }
    
    try:
        f = mutagen.File(filepath)
        if f is not None:
            if hasattr(f, 'info'):
                meta['sample_rate'] = getattr(f.info, 'sample_rate', None)
                meta['bitrate'] = getattr(f.info, 'bitrate', None)
                meta['duration_seconds'] = getattr(f.info, 'length', None)

                # Derive codec from the mutagen file-object type, not f.info.
                # f.info class names vary (e.g. FLAC uses StreamInfo, MP3
                # uses MPEGInfo) while the top-level class names are stable.
                file_type = type(f).__name__
                if file_type == 'FLAC':
                    meta['codec'] = 'flac'
                    meta['bit_depth'] = getattr(f.info, 'bits_per_sample', None)
                elif file_type == 'OggOpus':
                    meta['codec'] = 'opus'
                elif file_type == 'MP3':
                    meta['codec'] = 'mp3'
                elif file_type == 'MP4':
                    meta['codec'] = 'aac'

                # Fallback to extension if type detection failed
                if not meta['codec']:
                    ext = filepath.suffix.lower()
                    ext_map = {
                        '.flac': 'flac',
                        '.opus': 'opus',
                        '.mp3': 'mp3',
                        '.m4a': 'aac',
                        '.aac': 'aac',
                        '.ogg': 'ogg',
                        '.wav': 'wav'
                    }
                    meta['codec'] = ext_map.get(ext)

            if hasattr(f, 'tags') and f.tags:
                def _get_tag(*keys) -> str:
                    """Try each key in order; return the first non-empty string found."""
                    for key in keys:
                        val = f.tags.get(key)
                        if val is not None:
                            item = val[0] if isinstance(val, (list, tuple)) else val
                            text = str(item).strip()
                            if text:
                                return text
                    return ""

                # Vorbis Comment (FLAC/OGG): lowercase keys
                # ID3 (MP3):                 TIT2 / TPE1 / TALB
                # MP4/M4A (AAC/ALAC):        ©nam / ©ART / ©alb  (© = \xa9)
                meta['title']  = _get_tag('title',  'TIT2', '\xa9nam')
                meta['artist'] = _get_tag('artist', 'TPE1', '\xa9ART')
                meta['album']  = _get_tag('album',  'TALB', '\xa9alb')
            
    except Exception as e:
        print(f"Error extracting metadata from {filepath}: {e}")
        
    return meta

def repair_file_metadata() -> Dict[str, Any]:
    """
    Re-extracts and writes metadata for music_file records whose raw_meta
    field is blank (i.e. stored as ' |  | ').  This happens when the file
    was first discovered before the tag-reading code supported that codec's
    key format (e.g. MP4/M4A files that use ©nam/©ART/©alb keys).

    Safe to re-run: it only touches records with empty metadata.
    """
    from src.core.schema import COLL_FILE, MusicFile

    pb = get_pb_client()
    stats = {"checked": 0, "repaired": 0, "errors": []}

    EMPTY_COMBO = " |  | "
    try:
        records = pb.collection(COLL_FILE).get_full_list(
            query_params={"filter": f"{MusicFile.RAW_META}='{EMPTY_COMBO}'"}
        )
    except Exception as e:
        stats["errors"].append(f"Failed to fetch records: {e}")
        return stats

    stats["checked"] = len(records)
    print(f"STATUS: Found {stats['checked']} files with empty metadata.")

    for record in records:
        file_path_str = getattr(record, MusicFile.FILE_PATH, None)
        if not file_path_str:
            continue
        filepath = Path(file_path_str)
        if not filepath.exists():
            stats["errors"].append(f"File not found on disk: {file_path_str}")
            continue

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(extract_metadata, filepath)
                meta = future.result(timeout=FILE_TIMEOUT_SECONDS)
        except concurrent.futures.TimeoutError:
            stats["errors"].append(f"Timed out reading metadata for {file_path_str}")
            continue
        except Exception as e:
            stats["errors"].append(f"Metadata error for {file_path_str}: {e}")
            continue

        raw_title  = meta.get('title')  or ""
        raw_artist = meta.get('artist') or ""
        raw_album  = meta.get('album')  or ""
        new_combo  = f"{raw_title} | {raw_artist} | {raw_album}"

        if new_combo == EMPTY_COMBO:
            stats["errors"].append(f"Still no metadata after re-extraction: {file_path_str}")
            continue

        update_data = {MusicFile.RAW_META: new_combo}
        if meta.get('codec'):
            update_data['codec'] = meta['codec']

        pb.collection(COLL_FILE).update(record.id, update_data)
        print(f"STATUS: Repaired: {filepath.name} → {new_combo}")
        stats["repaired"] += 1

    print(f"STATUS: Done. Repaired {stats['repaired']} / {stats['checked']} files.")
    return stats


def run_discovery(pb: Optional[PocketBase] = None, ingest_folders: Optional[list[str]] = None) -> Dict[str, Any]:
    """
    Scans the ingest directories and inserts new files into PocketBase.
    Reads from the configured base ingest path.
    """
    base_path = Path(settings.ingest_base_path)
    if pb is None:
        pb = get_pb_client()
    
    new_files_count = 0
    updated_files_count = 0
    errors = []
    
    # Supported audio extensions
    VALID_EXTS = {'.flac', '.opus', '.mp3', '.m4a', '.aac', '.ogg', '.wav'}

    if ingest_folders is None:
        ingest_folders = [d.strip() for d in settings.ingest_dirs.split(',')]

    # ⚡ Bolt Optimization: Pre-fetch all files to avoid N+1 queries.
    # We only need id, file_path, and file_hash for discovery.
    # Impact: Reduces discovery time from O(N) database queries to O(1) query + O(1) lookup per file.
    try:
        all_records = pb.collection('music_file').get_full_list(
            query_params={"fields": "id,file_path,file_hash"}
        )
        existing_files_dict = {getattr(r, 'file_path'): r for r in all_records}
    except Exception as e:
        errors.append(f"Failed to pre-fetch files from PocketBase: {e}")
        return {
            "status": "error",
            "new_files": 0,
            "updated_files": 0,
            "errors": errors
        }

    for dir_name in ingest_folders:
        ingest_path = base_path / dir_name
        if not ingest_path.exists():
            continue
            
        print(f"STATUS: Scanning folder: {dir_name}")
        for root, _, files in os.walk(ingest_path):
            for file in files:
                filepath = Path(root) / file
                if filepath.suffix.lower() not in VALID_EXTS:
                    print(f"DEBUG: Skipping {filepath.name} with suffix {filepath.suffix}")
                    continue
                    
                try:
                    # stat_fingerprint uses os.stat() only — zero file reads, no CIFS blocking.
                    file_fingerprint = stat_fingerprint(filepath)

                    # Check if file exists in PocketBase
                    file_path_str = str(filepath)
                    existing_record = existing_files_dict.get(file_path_str)

                    if existing_record:
                        # File exists — check if size/mtime changed
                        existing_fp = getattr(existing_record, 'file_hash', None)
                        if existing_fp != file_fingerprint:
                            pb.collection('music_file').update(existing_record.id, {
                                'file_hash': file_fingerprint,
                                'quality_score': None  # Reset so analyze re-runs
                            })
                            updated_files_count += 1
                    else:
                        # New file
                        print(f"STATUS: New file discovered: {filepath.name}")
                        # metadata extraction safety net...
                        try:
                            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                                future = ex.submit(extract_metadata, filepath)
                                meta = future.result(timeout=FILE_TIMEOUT_SECONDS)
                        except concurrent.futures.TimeoutError:
                            errors.append(
                                f"Timed out reading metadata for {filepath} "
                                f"(>{FILE_TIMEOUT_SECONDS}s) — skipping"
                            )
                            continue

                        raw_title = meta.get('title') or ""
                        raw_artist = meta.get('artist') or ""
                        raw_album = meta.get('album') or ""

                        raw_combo = f"{raw_title} | {raw_artist} | {raw_album}"

                        pb.collection('music_file').create({
                            'source_dir': dir_name,
                            'file_path': file_path_str,
                            'file_hash': file_fingerprint,
                            'raw_title__raw_artist__raw_album': raw_combo,
                            'codec': meta['codec'],
                            'sample_rate': meta['sample_rate'],
                            'bit_depth': meta['bit_depth'],
                            'bitrate': int(meta['bitrate']) if meta['bitrate'] else None,
                            'duration_seconds': meta['duration_seconds'],
                            'is_primary': False
                        })
                        new_files_count += 1

                except Exception as e:
                    print(f"DEBUG: Processing error for {filepath.name}: {e}")
                    errors.append(f"Error processing {filepath}: {str(e)}")


    return {
        "status": "success",
        "new_files": new_files_count,
        "updated_files": updated_files_count,
        "errors": errors
    }
