import os
import hashlib
from pathlib import Path
from typing import Dict, Any, List
import mutagen
from pocketbase import PocketBase
from pocketbase.client import FileUpload

from src.core.config import settings

def get_pb_client() -> PocketBase:
    client = PocketBase(settings.pocketbase_url)
    client.admins.auth_with_password(
        settings.pocketbase_admin_email, 
        settings.pocketbase_admin_password
    )
    return client

def hash_file(filepath: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

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

                # Map codecs, sample_rate, bit_depth based on class
                class_name = type(f.info).__name__
                if class_name == 'OggOpusInfo':
                    meta['codec'] = 'opus'
                elif class_name == 'FLACInfo':
                    meta['codec'] = 'flac'
                    meta['bit_depth'] = getattr(f.info, 'bits_per_sample', None)
                elif class_name == 'MP3Info':
                    meta['codec'] = 'mp3'
                elif class_name == 'MP4Info':
                    meta['codec'] = 'aac'

            if hasattr(f, 'tags') and f.tags:
                meta['title'] = str(f.tags.get('title', [None])[0] or f.tags.get('TIT2', [None])[0] or "")
                meta['artist'] = str(f.tags.get('artist', [None])[0] or f.tags.get('TPE1', [None])[0] or "")
                meta['album'] = str(f.tags.get('album', [None])[0] or f.tags.get('TALB', [None])[0] or "")
            
    except Exception as e:
        print(f"Error extracting metadata from {filepath}: {e}")
        
    return meta

def run_discovery() -> Dict[str, Any]:
    """
    Scans the ingest directories and inserts new files into PocketBase.
    Reads from the configured base ingest path.
    """
    base_path = Path(settings.ingest_base_path)
    pb = get_pb_client()
    
    new_files_count = 0
    updated_files_count = 0
    errors = []
    
    # Supported audio extensions
    VALID_EXTS = {'.flac', '.opus', '.mp3', '.m4a', '.aac', '.ogg', '.wav'}

    ingest_folders = [d.strip() for d in settings.ingest_dirs.split(',')]

    for dir_name in ingest_folders:
        ingest_path = base_path / dir_name
        if not ingest_path.exists():
            continue
            
        for root, _, files in os.walk(ingest_path):
            for file in files:
                filepath = Path(root) / file
                if filepath.suffix.lower() not in VALID_EXTS:
                    continue
                    
                try:
                    file_hash = hash_file(filepath)
                    
                    # Check if file exists in PocketBase
                    file_path_str = str(filepath)
                    # Note: pocketbase filter syntax
                    records = pb.collection('music_file').get_list(
                        1, 1, {"filter": f"file_path='{file_path_str}'"}
                    )
                    
                    if records.items:
                        # File exists, check if hash changed
                        existing_record = records.items[0]
                        # Use getattr() for pocketbase python sdk custom records which use setattr
                        existing_hash = getattr(existing_record, 'file_hash', None)
                        if existing_hash != file_hash:
                            pb.collection('music_file').update(existing_record.id, {
                                'file_hash': file_hash,
                                'quality_score': None  # Reset quality score
                            })
                            updated_files_count += 1
                    else:
                        # New file
                        meta = extract_metadata(filepath)
                        raw_title = meta.get('title') or ""
                        raw_artist = meta.get('artist') or ""
                        raw_album = meta.get('album') or ""
                        
                        raw_combo = f"{raw_title} | {raw_artist} | {raw_album}"
                        
                        pb.collection('music_file').create({
                            'source_dir': dir_name,
                            'file_path': file_path_str,
                            'file_hash': file_hash,
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
                    errors.append(f"Error processing {filepath}: {str(e)}")

    return {
        "status": "success",
        "new_files": new_files_count,
        "updated_files": updated_files_count,
        "errors": errors
    }
