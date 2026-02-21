from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class PocketBaseModel(BaseModel):
    id: str
    created: str
    updated: str
    collectionId: str
    collectionName: str
    
    model_config = ConfigDict(extra="ignore")

class MusicRelease(PocketBaseModel):
    canonical_title: Optional[str] = None
    canonical_artist: Optional[str] = None
    canonical_album: Optional[str] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    mb_recording_id: Optional[str] = None
    mb_release_id: Optional[str] = None
    mb_status: str = "unknown"
    isrc: Optional[str] = None
    best_file: Optional[str] = None # Relation ID
    file_count: int = 0
    needs_review: bool = False

class MusicFile(PocketBaseModel):
    release: Optional[str] = None # Relation ID
    source_dir: str
    file_path: str
    file_hash: str
    acoustid_fp: Optional[str] = None
    raw_title__raw_artist__raw_album: Optional[str] = None
    codec: Optional[str] = None
    sample_rate: Optional[int] = None
    bit_depth: Optional[int] = None
    bitrate: Optional[int] = None
    duration_seconds: Optional[float] = None
    quality_score: Optional[float] = None
    quality_verdict: Optional[str] = None
    spectral_ceiling: Optional[float] = None
    is_primary: bool = False
    symlink_path: Optional[str] = None

class MusicMetadataSource(PocketBaseModel):
    file: str # Relation ID
    source: str # file_tags, info_json, musicbrainz, discogs, llm, manual
    field_name: str
    value: str
    confidence: int
