# music-curator

A self-hosted curation pipeline for Pakistani/South Asian music. Handles transliteration variance, upscaled lossy files masquerading as lossless, and tracks with no MusicBrainz entry.

## Architecture

Three layers, each doing what it does best:

| Layer | Tool | Role |
| --- | --- | --- |
| Data + UI | **PocketBase** | SQLite database, REST API, admin UI for browsing and editing the catalog |
| Compute | **Python FastAPI** | Fingerprinting, quality scoring, beets/mutagen tagging, symlink management |
| Orchestration | **n8n** | 15-minute cron, pipeline chaining, Discord notifications, retries |
| GPU (on-demand) | **Ollama on Windows** | LLM metadata normalization for transliteration and genre inference |

Communication between layers is HTTP only.

## Ingest Sources

Drop files in any of three directories on the NAS — the pipeline picks them up automatically:

```text
/mnt/user/main/downloads/unseeded/music/
├── yubal/      ← Yubal sync from YouTube Music (opus + .info.json)
├── tidal-dl/   ← Tidal/Qobuz FLAC downloads
└── adhoc/      ← Manual drops, any format
```

## How It Works

n8n runs every 15 minutes:

1. **Discover** — Walks ingest dirs, hashes files, inserts new ones into PocketBase with raw metadata
2. **Analyze** — Generates AcoustID fingerprints, scores audio quality, deduplicates across sources
3. **Tag** — beets matches against MusicBrainz/Discogs; gaps filled from `.info.json`; LLM cleans transliteration
4. **Symlink** — Best version of each track is symlinked into `/media/Music/` for Plex; Plex scan triggered
5. **MusicBrainz** (weekly) — Submits ISRCs, AcoustID fingerprints, and seeded release editor URLs for unmatched Pakistani recordings

## Quality Scoring

The pipeline catches upscaled files using audio signal analysis — not just container format:

| Signal | Weight |
| --- | --- |
| Effective spectral bandwidth (librosa) | 40% |
| FLAC Detective forensic score | 30% |
| Stated codec/bitrate | 20% |
| Source trust (tidal-dl > adhoc > yubal) | 10% |

Both versions of a duplicate stay on disk. Only the higher-scoring one is symlinked to Plex. Nothing is ever deleted.

## Plex Library

`/mnt/user/main/media/Music/` contains symlinks only. Both this directory and the ingest directories must be mounted into Plex's Docker container at the same absolute paths.

## Reviewing the Catalog

Open PocketBase's admin UI. Key workflows:

- **Duplicate review**: filter `works` by `needs_review = true`
- **Quality alerts**: filter `files` by `quality_verdict = fake` or `suspicious`
- **MusicBrainz queue**: filter `works` by `mb_status = pending`
- **Manual metadata edit**: click any field, save — n8n detects the change and re-tags the file and symlink automatically

## Hardware

| Node | Services |
| --- | --- |
| Proxmox LXC | Python FastAPI compute service + PocketBase |
| Proxmox (existing) | n8n (already deployed) |
| Windows PC (RTX 3080 Ti) | Ollama + Llama 3.1 8B on port 5000 |
| Unraid NAS | Ingest dirs, symlink library, Plex, Yubal |

## Documentation

See `notes/final-implementation-plan.md` for the full architecture spec: database schema, pipeline pseudocode, quality scoring algorithm, n8n workflow design, implementation roadmap, and risk register.

## Project Structure
```text
src/
├── api/          # Route handlers and main FastAPI config
├── core/         # Pydantic Settings and configurations 
├── models/       # PocketBase mappings
└── services/     # Stubs for audio logic, db connectors, etc
tests/            # pytest suite
systemd/          # Service daemon specifications
scripts/          # Setup and deployment scripts
```

## Running the API Locally
1. Activate the environment: `source .venv/bin/activate`
2. Run the application: `uvicorn src.api.main:app --reload`
3. Visit the auto-generated docs at `http://127.0.0.1:8000/docs`

## Existing Core Endpoints
- `POST /api/discover`: Scans ingest directories for new files.
- `POST /api/analyze`: Generates AcoustID and Quality scores.
- `POST /api/tag`: Enriches metadata via Beets and Ollama.
- `POST /api/symlink`: Renders the Active plex library.
- `POST /api/mb/batch-submit`: Auto-submits MusicBrainz data.
- `POST /api/mb/sync`: Fetches updated MBIDs.
- `POST /api/release/{id}/reanalyze`: Manual trigger for updates.
- `GET /api/health`: Validates the health of the system pipeline.

## Systemd
We use systemd to run this automatically. To deploy standard changes, use:
`./scripts/deploy_service.sh`

## Important Contribution Guidelines
If you are an AI assistant or human modifying this project, you **MUST** review the rules outlined in `AGENT_RULES.md`.
