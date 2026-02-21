from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import asyncio
from src.services.task_manager import task_manager

router = APIRouter()

@router.post("/discover")
async def discover_new_files(request: Request):
    """Scans the ingest directories and inserts new files into the database."""
    return StreamingResponse(
        task_manager.run_task("discover", "/api/discover", request),
        media_type="text/plain"
    )

@router.post("/analyze")
async def analyze_files(request: Request):
    """Generates AcoustID fingerprints, Librosa quality scores, and groups by release."""
    return StreamingResponse(
        task_manager.run_task("analyze", "/api/analyze", request),
        media_type="text/plain"
    )

@router.post("/tag")
async def tag_files() -> Dict[str, Any]:
    """Runs beets import, mutagen gap-fill, and Ollama LLM normalization."""
    return {"status": "accepted", "tagged": 0, "mb_matched": 0, "message": "Tagging skeleton"}

@router.post("/symlink")
async def create_symlinks(request: Request):
    """Rebuilds the active library path using symlinks to the best files."""
    return StreamingResponse(
        task_manager.run_task("symlink", "/api/symlink", request),
        media_type="text/plain"
    )

@router.post("/mb/batch-submit")
async def musicbrainz_submit() -> Dict[str, Any]:
    """Submits ISRCs and fingerprints to MusicBrainz."""
    return {"status": "accepted", "isrcs_submitted": 0, "message": "MB submit skeleton"}

@router.post("/mb/sync")
async def musicbrainz_sync() -> Dict[str, Any]:
    """Syncs updated MBIDs from MusicBrainz via beets."""
    return {"status": "accepted", "synced": 0, "new_mbids": 0, "message": "MB sync skeleton"}

@router.post("/release/{id}/reanalyze")
async def manual_reanalyze(id: str) -> Dict[str, Any]:
    """Triggers the analysis and tagging pipeline for a specific database release ID."""
    return {"status": "accepted", "release_id": id, "message": "Reanalyze skeleton"}

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Checks the health of the API wrapper, NFS mount, PocketBase, and Ollama."""
    return {"status": "ok", "broken_symlinks": 0, "message": "Health skeleton"}
