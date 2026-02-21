import logging
import pyacoustid
import librosa
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

def generate_acoustid(file_path: Path) -> Optional[str]:
    """Generates an AcoustID chromaprint fingerprint for the given audio file."""
    try:
        # fingerprint() returns (duration, fingerprint)
        duration, fp = pyacoustid.fingerprint_file(str(file_path))
        return fp.decode('utf-8') if isinstance(fp, bytes) else fp
    except Exception as e:
        logger.error(f"Failed to generate fingerprint for {file_path}: {e}")
        return None

def get_spectral_ceiling(file_path: Path) -> Optional[float]:
    """
    Computes the 99% spectral rolloff frequency to determine the true frequency ceiling.
    Helps detect fake upscaled FLAC files.
    """
    try:
        # Load audio (downmix to mono, target samplerate of 44.1kHz is fine for ceiling checks up to 22kHz)
        y, sr = librosa.load(str(file_path), sr=44100, mono=True)
        
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
    
    # Get all un-analyzed files (where acoustid_fp is null/empty)
    try:
        unanalyzed_records = pb.collection('music_file').get_full_list(
            query_params={"filter": "acoustid_fp='' || acoustid_fp=null"}
        )
    except Exception as e:
        logger.error(f"Failed to fetch unanalyzed files from pb: {e}")
        stats["errors"].append(str(e))
        return stats

    for record in unanalyzed_records:
        file_path_str = getattr(record, 'file_path', None)
        if not file_path_str:
            continue
            
        file_path = Path(file_path_str)
        if not file_path.exists():
            stats["errors"].append(f"File not found on disk: {file_path_str}")
            continue
            
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
                'acoustid_fp': fp or "FAILED",
                'spectral_ceiling': ceiling,
                'quality_score': score,
                'quality_verdict': verdict
            }
            pb.collection('music_file').update(record.id, update_data)
            stats["analyzed"] += 1
            
            if not fp:
                continue # Cannot deduplicate without footprint
                
            # 3. Deduplication Logic
            # Does this fingerprint already exist in a release?
            duplicate_files = pb.collection('music_file').get_list(
                1, 2, {"filter": f"acoustid_fp='{fp}' && id!='{record.id}'"}
            )
            
            target_release_id = None
            
            if duplicate_files.items:
                # We have a match! Attach to existing release
                existing_match = duplicate_files.items[0]
                target_release_id = getattr(existing_match, 'release', None)
                if target_release_id:
                    stats["merged_files"] += 1
                    
            if not target_release_id:
                # Completely new footprint, create new release parent
                # We'll use the raw string to extract rough placeholders
                raw_str = getattr(record, 'raw_title__raw_artist__raw_album', 'Unknown | Unknown | Unknown')
                parts = raw_str.split(' | ')
                title = parts[0] if len(parts) > 0 else "Unknown Title"
                artist = parts[1] if len(parts) > 1 else "Unknown Artist"
                album = parts[2] if len(parts) > 2 else "Unknown Album"
                
                new_release = pb.collection('music_release').create({
                    'canonical_title': title.strip(),
                    'canonical_artist': artist.strip(),
                    'canonical_album': album.strip(),
                    'mb_status': 'unknown',
                    'needs_review': True # Flag for fuzzy raw creation
                })
                target_release_id = new_release.id
                stats["new_releases"] += 1
                
            # Tie this file to the release parent
            pb.collection('music_file').update(record.id, {'release': target_release_id})
            
            # 4. Primary Election (Ranking)
            # Fetch all files tied to this release, sort by quality score descending
            siblings = pb.collection('music_file').get_full_list(
                query_params={"filter": f"release='{target_release_id}'", "sort": "-quality_score"}
            )
            
            if siblings:
                best_file_id = siblings[0].id
                
                # Link release to best file, adjust counts
                pb.collection('music_release').update(target_release_id, {
                    'best_file': best_file_id,
                    'file_count': len(siblings)
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
