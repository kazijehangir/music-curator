import hashlib
import logging
import acoustid
import librosa
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from src.core.schema import COLL_RELEASE, COLL_FILE, Release, MusicFile

logger = logging.getLogger(__name__)

import mutagen

def generate_acoustid(file_path: Path) -> Optional[str]:
    """
    Generates an AcoustID chromaprint fingerprint for the given audio file
    and returns a short SHA-256 hash of it.

    Optimization: First attempts to read the fingerprint from file metadata 
    (tags) to avoid expensive spectral analysis on network shares.
    """
    # 1. Try reading from metadata first
    try:
        f = mutagen.File(file_path)
        if f:
            fp = None
            # Common tag names for AcoustID fingerprints
            # beets/Picard use 'acoustid_fingerprint' (FLAC/Vorbis) 
            # or 'TXXX:Acoustid Fingerprint' (ID3/MP3)
            # iTunes/MP4 uses '----:com.apple.iTunes:Acoustid Fingerprint'
            tags_to_check = [
                'acoustid_fingerprint', 
                'TXXX:Acoustid Fingerprint', 
                '----:com.apple.iTunes:Acoustid Fingerprint'
            ]
            
            for tag in tags_to_check:
                if tag in f:
                    val = f[tag]
                    fp = val[0] if isinstance(val, list) else val
                    break
            
            if fp:
                raw = fp.decode('utf-8') if isinstance(fp, bytes) else str(fp)
                return hashlib.sha256(raw.encode()).hexdigest()[:16]
    except Exception as e:
        logger.debug(f"Metadata fingerprint lookup failed for {file_path}: {e}")

    # 2. Fallback to calculation
    try:
        # fingerprint() returns (duration, fingerprint)
        duration, fp = acoustid.fingerprint_file(str(file_path))
        raw = fp.decode('utf-8') if isinstance(fp, bytes) else fp
        # Shorten to a URL-safe 16-char hex digest for storage/filtering
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    except Exception as e:
        logger.error(f"Failed to generate fingerprint for {file_path}: {e}")
        return None

def get_spectral_ceiling(file_path: Path) -> Optional[float]:
    """
    Computes the 99% spectral rolloff frequency to determine the true frequency ceiling.
    Helps detect fake upscaled FLAC files.
    """
    try:
        # Load audio (downmix to mono, target sr=44100).
        # Optimization: Only process a 15-second snippet from the middle (offset=30s)
        # Analyzing the entire 5 minute file calculates millions of FFT frames and causes hangs
        y, sr = librosa.load(str(file_path), sr=44100, mono=True, offset=30.0, duration=15.0)
        
        # Calculate spectral rolloff (99% of energy lies below this frequency)
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.99)
        
        # Average the rolloff frequencies across the track
        avg_rolloff = float(np.mean(rolloff))
        return avg_rolloff
    except Exception as e:
        logger.error(f"Failed to analyze spectral ceiling for {file_path}: {e}")
        return None

def calculate_quality_score(
    codec: str, 
    bitrate: Optional[int], 
    bit_depth: Optional[int], 
    spectral_ceiling: Optional[float]
) -> Tuple[int, str]:
    """
    Calculates a 0-100 quality score and a verdict (authentic, lossy, fake) 
    based on codec expectations vs actual spectral ceiling.
    """
    score = 0
    verdict = "authentic"
    
    # 1. Base score derived from stated codec/format (max 60 points)
    if codec in ['flac', 'alac', 'wav']:
        score += 60
        if bit_depth and bit_depth >= 24:
            score += 10 # Bonus for 24-bit
    elif codec == 'opus':
        score += 40
        if bitrate and bitrate >= 128000:
            score += 10
    elif codec in ['mp3', 'aac', 'm4a']:
        score += 30
        if bitrate and bitrate >= 320000:
            score += 15
        elif bitrate and bitrate >= 192000:
            score += 5
    else:
        score += 20
        
    # 2. Spectral Analysis (max 40 points)
    if spectral_ceiling:
        if spectral_ceiling > 20000:
            score += 40
        elif spectral_ceiling > 18000:
            score += 30
        elif spectral_ceiling > 15000:
            score += 20
        else:
            score += 10
            
    # 3. Verdict Logic (Detecting fake upscales)
    if codec in ['flac', 'alac', 'wav']:
        # True lossless should generally peak over 19-20kHz.
        # If a FLAC cuts off drastically at 16kHz, it's almost certainly a 128kbps MP3 upscale.
        if spectral_ceiling and spectral_ceiling < 16500:
            score = max(0, score - 50) # Penalize heavily
            verdict = "fake"
        elif spectral_ceiling and spectral_ceiling < 19000:
            score = max(0, score - 20)
            verdict = "suspicious"
    else:
        verdict = "lossy"

    return min(100, score), verdict

def cleanup_orphaned_releases() -> Dict[str, Any]:
    """
    Deletes music_release rows that have no music_file pointing to them.

    Strategy (2 API calls + 1 call per orphan):
      1. Fetch all release IDs.
      2. Fetch all files and collect the set of referenced release IDs.
      3. Delete every release whose ID is not in the referenced set.
    """
    from src.services.discover import get_pb_client

    pb = get_pb_client()
    stats = {"checked": 0, "deleted": 0, "errors": []}

    # 1. All release IDs
    all_releases = pb.collection(COLL_RELEASE).get_full_list(
        query_params={"fields": "id"}
    )
    stats["checked"] = len(all_releases)
    print(f"STATUS: Found {stats['checked']} total releases.")

    # 2. All referenced release IDs (from music_file.release)
    all_files = pb.collection(COLL_FILE).get_full_list(
        query_params={"fields": "release", "filter": "release!=''"}
    )
    referenced_ids = {getattr(f, MusicFile.RELEASE, None) for f in all_files} - {None, ""}
    print(f"STATUS: {len(referenced_ids)} releases are referenced by at least one file.")

    # 3. Delete orphans
    orphan_ids = [r.id for r in all_releases if r.id not in referenced_ids]
    total_orphans = len(orphan_ids)
    print(f"STATUS: {total_orphans} orphaned releases to delete.")

    for i, release_id in enumerate(orphan_ids):
        try:
            pb.collection(COLL_RELEASE).delete(release_id)
            stats["deleted"] += 1
            if (i + 1) % 50 == 0:
                print(f"STATUS: Deleted {i + 1}/{total_orphans}...")
        except Exception as e:
            msg = f"Failed to delete release {release_id}: {e}"
            logger.error(msg)
            stats["errors"].append(msg)

    print(f"STATUS: Done. Deleted {stats['deleted']} orphaned releases.")
    return stats


def run_analysis() -> Dict[str, Any]:
    """
    Full pipeline to analyze un-fingerprinted files in PocketBase, 
    score them, and deduplicate into releases.
    """
    from src.core.config import settings
    from pocketbase import PocketBase
    
    pb = PocketBase(settings.pocketbase_url)
    pb.admins.auth_with_password(
        settings.pocketbase_admin_email, 
        settings.pocketbase_admin_password
    )
    
    # Track stats
    stats = {"analyzed": 0, "new_releases": 0, "merged_files": 0, "errors": []}
    
    # Get all un-analyzed files or files needing fingerprint migration
    # We pick up: 
    # 1. New files (fp is empty/null)
    # 2. Failed previous attempts (fp is 'FAILED')
    # 3. Old long fingerprints (not 16 chars)
    try:
        unanalyzed_records = pb.collection('music_file').get_full_list(
            query_params={"filter": "acoustid_fp='' || acoustid_fp=null || acoustid_fp='FAILED'"}
        )
    except Exception as e:
        logger.error(f"Failed to fetch unanalyzed files from pb: {e}")
        stats["errors"].append(str(e))
        return stats

    total = len(unanalyzed_records)
    print(f"STATUS: Found {total} files needing analysis.")

    for i, record in enumerate(unanalyzed_records):
        file_path_str = getattr(record, 'file_path', None)
        if not file_path_str:
            continue
            
        file_path = Path(file_path_str)
        if not file_path.exists():
            stats["errors"].append(f"File not found on disk: {file_path_str}")
            continue
            
        print(f"STATUS: Analyzing [{i+1}/{total}] {file_path.name}")
        try:
            # 1. Forensic Processing
            fp = generate_acoustid(file_path)
            ceiling = get_spectral_ceiling(file_path)
            
            codec = getattr(record, 'codec', '')
            bitrate = getattr(record, 'bitrate', None)
            bit_depth = getattr(record, 'bit_depth', None)
            
            score, verdict = calculate_quality_score(codec, bitrate, bit_depth, ceiling)
            
            # 2. Update File Record
            update_data = {
                MusicFile.ACOUSTID_FP: fp or "FAILED",
                MusicFile.SPECTRAL_CEILING: ceiling,
                MusicFile.QUALITY_SCORE: score,
                MusicFile.QUALITY_VERDICT: verdict
            }
            pb.collection(COLL_FILE).update(record.id, update_data)
            stats["analyzed"] += 1
            
            if not fp:
                continue # Cannot deduplicate without footprint
                
            # 3. Deduplication Logic
            duplicate_files = pb.collection(COLL_FILE).get_list(
                1, 2, {"filter": f"{MusicFile.ACOUSTID_FP}='{fp}' && id!='{record.id}'"}
            )

            # Preserve existing release assignment — re-analyzing a file (e.g.
            # after a FAILED fingerprint) must not create a duplicate release.
            target_release_id = getattr(record, MusicFile.RELEASE, None) or None

            if duplicate_files.items:
                # We have a match! Attach to existing release
                existing_match = duplicate_files.items[0]
                target_release_id = getattr(existing_match, 'release', None)
                if target_release_id:
                    stats["merged_files"] += 1
                    
            if not target_release_id:
                # Completely new fingerprint — create new release parent.
                # The raw combo field holds "title | artist | album" from mutagen.
                # For untagged files (common with Yubal opus downloads), all three
                # parts may be empty strings. We fall back to the filename stem for
                # title so the release has something meaningful to display.
                raw_str = getattr(record, MusicFile.RAW_META, '') or ''
                parts = [p.strip() for p in raw_str.split(' | ')]

                title  = (parts[0] if len(parts) > 0 and parts[0] else '') or Path(file_path_str).stem
                artist = (parts[1] if len(parts) > 1 and parts[1] else '') or 'Unknown Artist'
                album  = (parts[2] if len(parts) > 2 and parts[2] else '') or ''

                new_release = pb.collection(COLL_RELEASE).create({
                    Release.TITLE: title,
                    Release.ARTIST: artist,
                    Release.ALBUM: album,
                    Release.MB_STATUS: 'unknown',
                    Release.NEEDS_REVIEW: True
                })
                target_release_id = new_release.id
                stats["new_releases"] += 1
                
            # Tie this file to the release parent
            pb.collection(COLL_FILE).update(record.id, {MusicFile.RELEASE: target_release_id})
            
            # 4. Primary Election (Ranking)
            # Fetch all files tied to this release, sort by quality score descending
            siblings = pb.collection(COLL_FILE).get_full_list(
                query_params={"filter": f"{MusicFile.RELEASE}='{target_release_id}'", "sort": f"-{MusicFile.QUALITY_SCORE}"}
            )

            if siblings:
                best_file_id = siblings[0].id
                pb.collection(COLL_RELEASE).update(target_release_id, {
                    Release.BEST_FILE: best_file_id,
                    Release.FILE_COUNT: len(siblings)
                })
                
                # Flag the specific primary file loop
                for sib in siblings:
                    is_p = (sib.id == best_file_id)
                    curr_p = getattr(sib, 'is_primary', False)
                    if curr_p != is_p:
                        pb.collection('music_file').update(sib.id, {'is_primary': is_p})
                        
        except Exception as e:
            logger.error(f"Error analyzing {file_path_str}: {e}")
            stats["errors"].append(f"Error processing {file_path_str}: {e}")

    return stats
