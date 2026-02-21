from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.post("/discover")
def discover_new_files() -> Dict[str, Any]:
    """Scans the ingest directories and inserts new files into the database."""
    from src.services.discover import run_discovery
    
    try:
        result = run_discovery()
        return {
            "status": "success", 
            "new_files": result["new_files"], 
            "updated_files": result["updated_files"],
            "errors": result["errors"]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/analyze")
def analyze_files() -> Dict[str, Any]:
    """Generates AcoustID fingerprints, Librosa quality scores, and groups by release."""
    from src.services.analyze import run_analysis
    try:
        result = run_analysis()
        return {
            "status": "success",
            "analyzed": result.get("analyzed", 0),
            "new_releases": result.get("new_releases", 0),
            "merged_files": result.get("merged_files", 0),
            "errors": result.get("errors", [])
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/tag")
async def tag_files() -> Dict[str, Any]:
    """Runs beets import, mutagen gap-fill, and Ollama LLM normalization."""
    return {"status": "accepted", "tagged": 0, "mb_matched": 0, "message": "Tagging skeleton"}

@router.post("/symlink")
async def create_symlinks() -> Dict[str, Any]:
    """Rebuilds the active library path using symlinks to the best files."""
    return {"status": "accepted", "created": 0, "plex_scan_triggered": False, "message": "Symlink skeleton"}

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
