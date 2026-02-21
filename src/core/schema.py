"""
Canonical PocketBase schema constants for music-curator.

This file is the single source of truth for all PocketBase collection names
and field names. Always import from here — never hardcode strings elsewhere.
If PocketBase schema changes, update this file and the compiler will surface
every broken reference.
"""

# ── Collection names ──────────────────────────────────────────────────────────

COLL_RELEASE = "music_release"
COLL_FILE = "music_file"
COLL_METADATA_SOURCE = "music_metadata_source"

# ── music_release fields ──────────────────────────────────────────────────────
# Actual PocketBase column names (from Admin UI).
# NB: these are title/artist/album — NOT canonical_title etc.

class Release:
    TITLE = "title"
    ARTIST = "artist"
    ALBUM = "album"
    GENRE = "genre"
    LANGUAGE = "language"
    MB_RECORDING_ID = "mb_recording_id"
    MB_RELEASE_ID = "mb_release_id"
    MB_STATUS = "mb_status"          # unknown | matched | pending | submitted | synced
    ISRC = "isrc"
    BEST_FILE = "best_file"          # relation → music_file
    FILE_COUNT = "file_count"
    NEEDS_REVIEW = "needs_review"

# ── music_file fields ─────────────────────────────────────────────────────────

class MusicFile:
    RELEASE = "release"              # relation → music_release
    SOURCE_DIR = "source_dir"
    FILE_PATH = "file_path"
    FILE_HASH = "file_hash"
    ACOUSTID_FP = "acoustid_fp"
    RAW_META = "raw_title__raw_artist__raw_album"   # "title | artist | album" combo
    CODEC = "codec"
    SAMPLE_RATE = "sample_rate"
    BIT_DEPTH = "bit_depth"
    BITRATE = "bitrate"
    DURATION_SECONDS = "duration_seconds"
    QUALITY_SCORE = "quality_score"
    QUALITY_VERDICT = "quality_verdict"  # authentic | warning | suspicious | fake | lossy
    SPECTRAL_CEILING = "spectral_ceiling"
    IS_PRIMARY = "is_primary"
    SYMLINK_PATH = "symlink_path"

# ── music_metadata_source fields ──────────────────────────────────────────────

class MetadataSource:
    FILE = "file"                    # relation → music_file
    SOURCE = "source"                # file_tags | info_json | musicbrainz | discogs | llm | manual
    FIELD_NAME = "field_name"
    VALUE = "value"
    CONFIDENCE = "confidence"        # 0-100
