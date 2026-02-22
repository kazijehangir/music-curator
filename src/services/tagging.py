import logging
import json
import httpx
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.core.config import settings
from src.core.schema import COLL_RELEASE, COLL_FILE, COLL_METADATA_SOURCE, Release, MusicFile, MetadataSource
from src.models.metadata import LLMMetadataResponse
import mutagen
import subprocess

logger = logging.getLogger(__name__)

# Confidence levels
CONF_MANUAL = 100
CONF_MB = 95
CONF_FILE_TAGS = 80
CONF_LLM = 70
CONF_SIDECAR = 60

def run_tagging() -> Dict[str, Any]:
    """
    Main entrypoint for the /api/tag endpoint.
    Retrieves all releases that need tagging and runs the 3-pass pipeline.
    """
    from src.services.discover import get_pb_client
    pb = get_pb_client()
    
    stats = {"tagged": 0, "mb_matched": 0, "llm_processed": 0, "errors": []}
    
    try:
        # Fetch releases that we haven't tagged yet (mb_status='unknown') or need review
        # We also pick up those where mb_status is entirely empty if applicable
        releases = pb.collection(COLL_RELEASE).get_full_list(
            query_params={"filter": f"{Release.MB_STATUS}='unknown' || {Release.NEEDS_REVIEW}=true"}
        )
    except Exception as e:
        logger.error(f"Failed to fetch releases for tagging: {e}")
        stats["errors"].append(str(e))
        return stats
        
    for idx, r in enumerate(releases):
        print(f"STATUS: Tagging release {r.id} ({idx+1}/{len(releases)})")
        try:
            success = process_release(pb, r, stats)
            if success:
                stats["tagged"] += 1
        except Exception as e:
            msg = f"Error tagging release {r.id}: {e}"
            logger.error(msg)
            stats["errors"].append(msg)
            
    print(f"STATUS: Tagging complete. Processed {stats['tagged']} releases.")
    return stats

def process_release(pb, release, stats: Dict[str, Any]) -> bool:
    # Get all files for this release
    files = pb.collection(COLL_FILE).get_full_list(
        query_params={"filter": f"{MusicFile.RELEASE}='{release.id}'"}
    )
    if not files:
        return False
        
    # Find the primary file, or default to the first
    primary_file = next((f for f in files if getattr(f, MusicFile.IS_PRIMARY, False)), files[0])
    
    # Pass 1: Beets (MB)
    mb_id = _pass_1_beets(primary_file)
    if mb_id:
        # Save MB source entries
        pb.collection(COLL_METADATA_SOURCE).create({
            MetadataSource.FILE: primary_file.id,
            MetadataSource.SOURCE: "musicbrainz",
            MetadataSource.FIELD_NAME: Release.MB_RELEASE_ID,
            MetadataSource.VALUE: mb_id,
            MetadataSource.CONFIDENCE: CONF_MB
        })
        pb.collection(COLL_RELEASE).update(release.id, {Release.MB_STATUS: "matched"})
        stats["mb_matched"] += 1
    
    # Pass 2: Sidecars
    _pass_2_sidecars(pb, release.id, files)
    
    # Pass 3: LLM Normalization (If no high confidence matches exist yet, e.g. from Pass 1)
    # If no MB ID was matched, we rely heavily on LLM
    if not mb_id:
        _pass_3_llm(pb, release.id, primary_file, stats)
    
    # Final step: Resolve best metadata and write to tags
    _resolve_and_write_tags(pb, release.id, primary_file)
    
    # Clear needs_review flag
    pb.collection(COLL_RELEASE).update(release.id, {Release.NEEDS_REVIEW: False})
    
    return True

def _pass_1_beets(primary_file) -> Optional[str]:
    # Placeholder for actual beets integration
    # Ideally runs `beet import -q` on the primary_file.file_path and extracts the MBID
    return None

def _pass_2_sidecars(pb, release_id: str, files: List[Any]):
    # Try to find .info.json next to files and extract YouTube metadata
    for file_record in files:
        file_path_str = getattr(file_record, MusicFile.FILE_PATH, None)
        if not file_path_str:
            continue
            
        file_path = Path(file_path_str)
        info_json_path = file_path.with_name(f"{file_path.stem}.info.json")
        if info_json_path.exists():
            try:
                with open(info_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                title = data.get('track') or data.get('title')
                artist = data.get('artist') or data.get('uploader')
                
                if title:
                    pb.collection(COLL_METADATA_SOURCE).create({
                        MetadataSource.FILE: file_record.id,
                        MetadataSource.SOURCE: "info_json",
                        MetadataSource.FIELD_NAME: Release.TITLE,
                        MetadataSource.VALUE: title,
                        MetadataSource.CONFIDENCE: CONF_SIDECAR
                    })
                if artist:
                    pb.collection(COLL_METADATA_SOURCE).create({
                        MetadataSource.FILE: file_record.id,
                        MetadataSource.SOURCE: "info_json",
                        MetadataSource.FIELD_NAME: Release.ARTIST,
                        MetadataSource.VALUE: artist,
                        MetadataSource.CONFIDENCE: CONF_SIDECAR
                    })
            except Exception as e:
                logger.error(f"Failed to read info.json for {file_path}: {e}")

def _pass_3_llm(pb, release_id: str, primary_file, stats: Dict[str, Any]):
    # Get raw metadata (e.g. filename or raw mutagen tags)
    raw_meta = getattr(primary_file, MusicFile.RAW_META, None)
    if not raw_meta:
        return
        
    prompt = f"Parse the following raw music track metadata into title, artist, album, genre, and language: '{raw_meta}'. Ensure to transliterate south asian text to Latin script."
    
    payload = {
        "model": "llama-3.1-8b", # Requires checking user's exact model
        "messages": [
            {"role": "system", "content": "You are a music metadata parsing assistant. Return a JSON object containing keys: 'title', 'artist', 'album', 'genre', 'language'."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"} # Use json_object response format
    }
    
    try:
        response = httpx.post(
            f"{settings.lm_studio_url}/chat/completions",
            json=payload,
            timeout=45.0
        )
        response.raise_for_status()
        result = response.json()
        
        # Parse output
        content = result['choices'][0]['message']['content']
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        parsed = LLMMetadataResponse.model_validate_json(content)
        
        # Save results to PocketBase
        fields_to_save = {
            Release.TITLE: parsed.title,
            Release.ARTIST: parsed.artist,
            Release.ALBUM: parsed.album,
            Release.GENRE: parsed.genre,
            Release.LANGUAGE: parsed.language
        }
        
        for field, value in fields_to_save.items():
            if value:
                pb.collection(COLL_METADATA_SOURCE).create({
                    MetadataSource.FILE: primary_file.id,
                    MetadataSource.SOURCE: "llm",
                    MetadataSource.FIELD_NAME: field,
                    MetadataSource.VALUE: value,
                    MetadataSource.CONFIDENCE: CONF_LLM
                })
        stats["llm_processed"] += 1
                
    except Exception as e:
        msg = f"LLM normalization failed for {raw_meta}: {e}"
        logger.error(msg)
        stats.setdefault("errors", []).append(msg)

def _resolve_and_write_tags(pb, release_id: str, primary_file):
    # Query all metadata sources using primary file ID
    try:
        sources = pb.collection(COLL_METADATA_SOURCE).get_full_list(
            query_params={"filter": f"{MetadataSource.FILE}='{primary_file.id}'"}
        )
        
        best_tags = {}
        highest_conf = {}
        
        for s in sources:
            field = getattr(s, MetadataSource.FIELD_NAME, None)
            conf = getattr(s, MetadataSource.CONFIDENCE, 0)
            val = getattr(s, MetadataSource.VALUE, None)
            
            if not field or not val:
                continue
                
            if field not in highest_conf or conf > highest_conf[field]:
                highest_conf[field] = conf
                best_tags[field] = val
                
        # Update Release canonical fields
        if best_tags:
            # We must map generic title/artist fields to 'canonical' prefixed fields if needed based on schema?
            # Actually, `src/core/schema.py` defines `Release.TITLE` as `"title"` directly. Let's use it as is.
            pb.collection(COLL_RELEASE).update(release_id, best_tags)
            
            # Write to mutagen
            _write_mutagen_tags(getattr(primary_file, MusicFile.FILE_PATH), best_tags)
            
    except Exception as e:
        logger.error(f"Error resolving tags for {release_id}: {e}")

def _write_mutagen_tags(file_path: str, tags: Dict[str, Any]):
    try:
        f = mutagen.File(file_path, easy=True)
        if f is None:
            return
            
        mapping = {
            Release.TITLE: "title",
            Release.ARTIST: "artist",
            Release.ALBUM: "album",
            Release.GENRE: "genre",
        }
        
        changed = False
        for pb_field, mut_field in mapping.items():
            if pb_field in tags and tags[pb_field]:
                f[mut_field] = tags[pb_field]
                changed = True
                
        if changed:
            f.save()
            logger.info(f"Updated tags for {file_path}")
            
    except Exception as e:
        logger.error(f"Failed to write audio tags to {file_path}: {e}")
