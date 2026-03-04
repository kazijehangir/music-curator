import logging
import json
import re
import httpx
import sys
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
CONF_ADHOC = 40

# Source-directory to confidence mapping for raw file tags
_SOURCE_DIR_CONFIDENCE = {
    "tidal-dl": CONF_FILE_TAGS,  # 80 — commercial tags, usually correct
    "yubal":    CONF_SIDECAR,    # 60 — yt-dlp titles are good, albums/genre weak
    "adhoc":    CONF_ADHOC,      # 40 — unknown provenance
}

# Patterns to strip from filenames / titles before sending to the LLM.
_JUNK_PATTERN = re.compile(
    r'\s*[\(\[]'
    r'(?:official\s+(?:audio|video|music\s+video|lyric\s+video|hd)|'
    r'lyrics?|full\s+(?:song|audio|video)|hd|4k|128\s*kbps|320\s*kbps|'
    r'remaster(?:ed)?|explicit|clean\s+version|radio\s+edit)'
    r'[\)\]]'
    r'|\s+-\s+(?:official\s+(?:audio|video|music\s+video|lyric\s+video))',
    re.IGNORECASE,
)

def run_tagging(pb: Optional[Any] = None) -> Dict[str, Any]:
    """
    Main entrypoint for the /api/tag endpoint.
    Retrieves all releases that need tagging and runs the 3-pass pipeline.
    """
    if pb is None:
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

    # Pass 0: Seed raw file tags as provenance-tracked metadata_source records.
    # This runs first so every subsequent pass can compete on confidence rather
    # than the file-tag data silently losing because it was never registered.
    _pass_0_file_tags(pb, release.id, files)

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
        print(f"DEBUG: Starting Pass 3 (LLM) for release {release.id}")
        _pass_3_llm(pb, release.id, primary_file, stats)
    else:
        print(f"DEBUG: Skipping Pass 3 (LLM) because MB match exists: {mb_id}")
    
    # Final step: Resolve best metadata and write to tags
    _resolve_and_write_tags(pb, release.id, primary_file)
    
    # Clear needs_review flag
    pb.collection(COLL_RELEASE).update(release.id, {Release.NEEDS_REVIEW: False})
    
    return True

def _pass_0_file_tags(pb, release_id: str, files: List[Any]):
    """
    Seed raw file tags (extracted by discover) into music_metadata_source.

    discover.py stores title/artist/album as a pipe-separated combo in
    raw_title__raw_artist__raw_album. Without this pass those values are
    invisible to the confidence-based resolution system, so an LLM error
    could silently override a correct file tag with no way to win back.

    Confidence is assigned by source directory:
      tidal-dl → 80 (commercial tags, usually correct)
      yubal    → 60 (yt-dlp, good titles, weak genre/album)
      adhoc    → 40 (unknown provenance)
    """
    for file_record in files:
        raw_combo = getattr(file_record, MusicFile.RAW_META, None)
        if not raw_combo or not raw_combo.replace('|', '').strip():
            continue  # No embedded tags — nothing to seed

        parts = [p.strip() for p in raw_combo.split(' | ')]
        raw_title  = parts[0] if len(parts) > 0 else ""
        raw_artist = parts[1] if len(parts) > 1 else ""
        raw_album  = parts[2] if len(parts) > 2 else ""

        if not (raw_title or raw_artist or raw_album):
            continue

        source_dir = getattr(file_record, MusicFile.SOURCE_DIR, "adhoc") or "adhoc"
        confidence = _SOURCE_DIR_CONFIDENCE.get(source_dir, CONF_ADHOC)

        for field, value in [
            (Release.TITLE,  raw_title),
            (Release.ARTIST, raw_artist),
            (Release.ALBUM,  raw_album),
        ]:
            if value:
                try:
                    pb.collection(COLL_METADATA_SOURCE).create({
                        MetadataSource.FILE:       file_record.id,
                        MetadataSource.SOURCE:     "file_tags",
                        MetadataSource.FIELD_NAME: field,
                        MetadataSource.VALUE:      value,
                        MetadataSource.CONFIDENCE: confidence,
                    })
                except Exception as e:
                    logger.warning(f"Pass 0: could not seed {field} for file {file_record.id}: {e}")


def _pass_1_beets(primary_file) -> Optional[str]:
    file_path = getattr(primary_file, MusicFile.FILE_PATH, None)
    if not file_path:
        return None
        
    try:
        beet_bin = str(Path(sys.executable).parent / "beet")
        # SECURITY: Add '--' separator before positional path argument
        # to prevent command argument injection from filenames starting with hyphens.
        cmd = [beet_bin, "import", "-q", "-C", "-s", "--", str(file_path)]
        subprocess.run(cmd, capture_output=True, text=True)
        
        f = mutagen.File(file_path)
        if f is not None:
            # Check common MusicBrainz tags across codecs
            tags_to_check = ['musicbrainz_trackid', 'TXXX:MusicBrainz Release Track Id', '----:com.apple.iTunes:MusicBrainz Track Id']
            for tag in tags_to_check:
                if tag in f:
                    val = f[tag]
                    return str(val[0] if isinstance(val, list) else val)
    except Exception as e:
        logger.error(f"Beets pass failed for {file_path}: {e}")
        
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
                album = data.get('album')
                
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
                if album:
                    pb.collection(COLL_METADATA_SOURCE).create({
                        MetadataSource.FILE: file_record.id,
                        MetadataSource.SOURCE: "info_json",
                        MetadataSource.FIELD_NAME: Release.ALBUM,
                        MetadataSource.VALUE: album,
                        MetadataSource.CONFIDENCE: CONF_SIDECAR
                    })
            except Exception as e:
                logger.error(f"Failed to read info.json for {file_path}: {e}")

def _pass_3_llm(pb, release_id: str, primary_file, stats: Dict[str, Any]):
    """
    Pass 3: LLM normalization via Ollama/LM Studio.

    Builds the richest possible structured input for the LLM by:
      1. Using the highest-confidence value per field gathered so far
         (from Pass 0 file tags and Pass 2 sidecars).
      2. Falling back to the release record's title/artist/album when
         no metadata_source entries exist yet.
      3. When the fallback title looks like a yt-dlp filename stem
         (e.g. "Tum Aik Gorakh Dhanda Ho - Nescafe Basement") and the
         artist is unknown, splitting the title on " - " to surface the
         show/album name as a separate field — giving the LLM the context
         it needs for genre inference.
    """
    # Collect the best value per field from existing metadata_source records.
    debug_id = f"{primary_file.id}"
    try:
        sources = pb.collection(COLL_METADATA_SOURCE).get_full_list(
            query_params={"filter": f"{MetadataSource.FILE}='{primary_file.id}'"}
        )
        best_tags: Dict[str, Any] = {}
        highest_conf: Dict[str, int] = {}
        for s in sources:
            field = getattr(s, MetadataSource.FIELD_NAME, None)
            conf  = getattr(s, MetadataSource.CONFIDENCE, 0)
            val   = getattr(s, MetadataSource.VALUE, None)
            if field and val:
                if field not in highest_conf or conf > highest_conf[field]:
                    highest_conf[field] = conf
                    best_tags[field] = val
    except Exception as e:
        logger.error(f"Error fetching existing metadata for LLM pass: {e}")
        best_tags = {}

    current_title  = best_tags.get(Release.TITLE,  "")
    current_artist = best_tags.get(Release.ARTIST, "")
    current_album  = best_tags.get(Release.ALBUM,  "")

    llm_input_label = ""  # Used in exception message to avoid NameError

    if current_title or current_artist or current_album:
        # At least one field is known — use structured input directly.
        llm_input_label = f"{current_title} / {current_artist}"
        input_text = f"Title: {current_title} | Artist: {current_artist} | Album: {current_album}"
        print(f"DEBUG: Using gathered metadata for LLM: '{input_text}'")
    else:
        # No metadata_source entries yet — fall back to the release record.
        raw_meta = getattr(primary_file, MusicFile.RAW_META, None)
        print(f"DEBUG: Raw meta for {debug_id}: '{raw_meta}'")

        if not raw_meta or not raw_meta.replace('|', '').strip():
            try:
                rel = pb.collection(COLL_RELEASE).get_one(release_id)
                raw_meta = (
                    f"{getattr(rel, Release.TITLE, '')} | "
                    f"{getattr(rel, Release.ARTIST, '')} | "
                    f"{getattr(rel, Release.ALBUM, '')}"
                )
                print(f"DEBUG: Using fallback raw_meta from release: '{raw_meta}'")
            except Exception as e:
                print(f"DEBUG: Fallback failed: {e}")
                return

        if not raw_meta.replace('|', '').strip():
            print("DEBUG: Even fallback meta is empty, skipping LLM")
            return

        # Parse the pipe-separated combo into components.
        parts          = [p.strip() for p in raw_meta.split(' | ')]
        parsed_title   = parts[0] if len(parts) > 0 else ""
        parsed_artist  = parts[1] if len(parts) > 1 else ""
        parsed_album   = parts[2] if len(parts) > 2 else ""

        # When artist is unknown and the title looks like a yt-dlp filename
        # stem (e.g. "Tum Aik Gorakh Dhanda Ho - Nescafe Basement"), split on
        # the LAST " - " to separate title from show/album.  This surfaces
        # "Nescafe Basement" as a distinct field, which the LLM can use to
        # infer genre (Sufi/folk showcase) instead of guessing blindly.
        artist_is_unknown = not parsed_artist or parsed_artist in ("Unknown Artist", "Unknown", "")
        if artist_is_unknown and " - " in parsed_title and not parsed_album:
            title_parts   = [p.strip() for p in parsed_title.rsplit(" - ", 1)]
            clean_title   = _JUNK_PATTERN.sub("", title_parts[0]).strip()
            clean_show    = _JUNK_PATTERN.sub("", title_parts[-1]).strip()
            parsed_title  = clean_title or parsed_title
            parsed_album  = clean_show
            print(f"DEBUG: Split filename title → title='{parsed_title}', show/album='{parsed_album}'")

        llm_input_label = f"{parsed_title} / {parsed_artist}"
        input_text = (
            f"Title: {parsed_title} | "
            f"Artist: {parsed_artist or 'Unknown'} | "
            f"Album/Show: {parsed_album}"
        )

    prompt = (
        f"Analyze the following raw music track metadata: '{input_text}'.\n\n"
        "Return a JSON object with 'title', 'artist', 'album', 'genre', and 'language'.\n"
        "RULES:\n"
        "1. Context: This is a Pakistani/South Asian music library. "
        "Use ALL available context — title, artist, AND album/show — to infer the correct genre.\n"
        "2. Genre Classification:\n"
        "   - 'Sufi Qawwali': Abida Parveen, Nusrat Fateh Ali Khan, Rahat Fateh Ali Khan, "
        "Ali Sethi, Tina Sani. Key indicators: Mentions of 'Coke Studio' or 'Nescafe Basement' "
        "combined with traditional/devotional singers. Songs like 'Aaqa', 'Hasrat' (if spiritual), "
        "'Tum Aik Gorakh Dhanda Ho'.\n"
        "   - 'Ghazal': Mehdi Hassan, Ghulam Ali, Jagjit Singh, Farida Khanum.\n"
        "   - 'Urdu Hip Hop': aleemrk, Talha Anjum, Talha Yunus, Young Stunners, Maanu, Faris Shafi.\n"
        "   - 'Pakistani Pop': Atif Aslam, Hadiqa Kiyani, Ali Zafar, Strings, Vital Signs.\n"
        "   - 'Folk': Reshma, Arif Lohar, Zarsanga.\n"
        "   DO NOT output generic terms like 'Unknown', 'Music', or 'World Music'.\n"
        "3. Language: Infer the primary language (e.g. 'Urdu', 'Punjabi', 'Hindi', 'English', 'Sindhi', 'Persian').\n"
        "4. Title Case: Apply proper title case (e.g. 'HASRAT' → 'Hasrat').\n"
        "5. Cleanup: Transliterate non-Latin script to Latin. "
        "Remove garbage suffixes like '(Official Audio)', '[128kbps]', 'Music Video', 'Lyrics', "
        "'(Official Music Video)', 'ft.', 'feat.' from title ONLY. Keep artist collaborators in the artist field.\n"
        "6. Album/Show: If the input specifies a show like 'Coke Studio Season 9' or 'Nescafe Basement', "
        "preserve it EXACTLY as the 'album'. Do not truncate it to just the show name if a season is provided."
    )

    payload = {
        "model": settings.llm_model_name,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a music metadata parsing assistant specializing in Pakistani and "
                    "South Asian music. Return ONLY a valid JSON object with keys: "
                    "'title', 'artist', 'album', 'genre', 'language'. No markdown, no explanation."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
    }

    try:
        base_url = settings.lm_studio_url.rstrip('/')
        if not base_url.endswith('/v1'):
            base_url += '/v1'

        response = httpx.post(
            f"{base_url}/chat/completions",
            json=payload,
            timeout=45.0,
        )
        response.raise_for_status()
        result = response.json()

        if 'choices' not in result or not result['choices']:
            logger.error(f"LLM response missing 'choices': {result}")
            return

        content = result['choices'][0]['message']['content'].strip()

        # Strip markdown code fences if the model wraps its output.
        if content.startswith("```json"):
            content = content[len("```json"):]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            parsed = LLMMetadataResponse.model_validate_json(content)
        except Exception as ve:
            logger.error(
                f"Failed to validate LLM JSON for {release_id}: {ve}\nContent: {content}"
            )
            return

        fields_to_save = {
            Release.TITLE:    parsed.title,
            Release.ARTIST:   parsed.artist,
            Release.ALBUM:    parsed.album,
            Release.GENRE:    parsed.genre,
            Release.LANGUAGE: parsed.language,
        }

        for field, value in fields_to_save.items():
            if value:
                pb.collection(COLL_METADATA_SOURCE).create({
                    MetadataSource.FILE:       primary_file.id,
                    MetadataSource.SOURCE:     "llm",
                    MetadataSource.FIELD_NAME: field,
                    MetadataSource.VALUE:      value,
                    MetadataSource.CONFIDENCE: CONF_LLM,
                })
        stats["llm_processed"] += 1

    except Exception as e:
        msg = f"LLM normalization failed for '{llm_input_label}': {e}"
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
