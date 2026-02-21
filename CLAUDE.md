# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A self-hosted music curation pipeline for Pakistani/South Asian music. Core challenges: MusicBrainz has poor coverage for this genre, transliteration varies wildly across sources, upscaled lossy files masquerade as lossless, and many tracks are YouTube/SoundCloud-only singles with no database entry.

The project is in the **implementation phase**. `notes/final-implementation-plan.md` is the source of truth for architecture. Earlier documents in `notes/` are superseded research.

## Architecture: Three Layers

**v3 principle**: each layer does what it's best at. No layer tries to do another's job.

| Layer | Tool | Responsibility |
| --- | --- | --- |
| Data + UI | PocketBase | Database (SQLite), REST API, admin UI for browsing/editing catalog, realtime event hooks |
| Compute | Python FastAPI service | Fingerprinting, spectral analysis, quality scoring, beets/mutagen tag ops, symlink management, MB seed generation |
| Orchestration | n8n | Cron scheduling, pipeline chaining, conditional logic, Discord notifications, retries |
| GPU (on-demand) | Ollama on Windows | LLM metadata normalization: transliteration, genre inference, MB seed data |

All layers communicate via HTTP only — no shared state, no file locks, no SSH.

## Hardware Topology

| Node | Role | Services |
| --- | --- | --- |
| Proxmox LXC | Curation Engine | Python FastAPI service + PocketBase. 2 cores, 2 GB RAM, 20 GB disk. |
| Proxmox (existing) | Orchestration | n8n (already deployed). Triggers compute endpoints, reads/writes PocketBase, sends Discord. |
| Windows PC (RTX 3080 Ti) | GPU API | Ollama + Llama 3.1 8B via FastAPI on port 5000. Called by Python service only. |
| Unraid NAS | Storage + Plex | Ingest directories, symlink library at `/media/Music/`, Plex Media Server, Yubal. |

## Directory Layout

```text
/mnt/user/main/downloads/unseeded/music/
├── yubal/              # Yubal writes here continuously (opus + .info.json sidecars)
├── tidal-dl/           # Bulk Tidal/Qobuz FLAC downloads
└── adhoc/              # Manual one-off drops, any structure

/mnt/user/main/media/Music/          # PLEX LIBRARY (symlinks only)
└── Artist Name/
    └── Album/
        └── 01 - Track.flac  → ../../../downloads/.../Track.flac
```

Plex's Docker container must mount both `/media/Music` and `/downloads/unseeded/music` at the same absolute paths the symlinks use, or symlinks break inside the container.

## Pipeline Flow

n8n runs a 15-minute cron. Each stage is an HTTP POST to the Python compute service:

```text
[Cron: */15] → POST /api/discover → POST /api/analyze → POST /api/tag → POST /api/symlink → Discord summary
```

**Stage 1 — Discover (`POST /api/discover`):** Walk all three ingest dirs, compute SHA-256 hashes, check against PocketBase. New files are inserted into the `files` collection with raw metadata from mutagen. For Yubal files, `.info.json` sidecars are also read. Returns `{ new_files, updated_files, skipped, errors }`.

**Stage 2 — Analyze (`POST /api/analyze`):** For each unanalyzed file: generate AcoustID fingerprint, run quality scoring, then deduplicate against existing works. Strong fingerprint match (correlation > 0.85) auto-groups; fuzzy metadata match (thefuzz `token_sort_ratio > 85` for title AND `> 90` for artist, duration ±10s) groups with `needs_review = true`. Re-evaluates `best_file` for each affected work. Returns `{ analyzed, new_works, merged_to_existing, needs_review }`.

**Stage 3 — Tag (`POST /api/tag`):** Three-pass enrichment for new/changed works:

1. `beet import -q` against MusicBrainz and Discogs (`quiet_fallback: asis`). Match confidence ≥ 0.80 → store MBID, insert `metadata_sources` with `confidence: 95`.
2. mutagen gap-fill from `.info.json` sidecars (confidence 60) and file tags (tidal-dl=80, yubal=60, adhoc=40).
3. LLM normalization via Ollama on Windows for unmatched works (transliteration, genre, Coke Studio parsing). Stored at `confidence: 70`.
Resolves canonical metadata by picking highest-confidence value per field from `metadata_sources`. Writes clean tags to the primary file.

**Stage 4 — Symlink (`POST /api/symlink`):** For works where the primary file changed: remove old symlink, create new one at `/media/Music/{canonical_artist}/{canonical_album or 'Singles'}/{canonical_title}.{ext}`, update `symlink_path` in PocketBase, trigger Plex library scan via plexapi.

**Stage 5 — MusicBrainz Contribution (weekly, `POST /api/mb/batch-submit` + `POST /api/mb/sync`):** See MusicBrainz section below.

## PocketBase Database Schema

Three collections model the core data:

**`works`** — An abstract song identity (e.g. "Pasoori" by Ali Sethi, regardless of how many files exist):

- `canonical_title`, `canonical_artist`, `canonical_album` — resolved best metadata
- `genre` (text), `language` (ISO 639-3: urd, pan, hin, eng)
- `mb_recording_id`, `mb_release_id`, `mb_status` (select: unknown | matched | pending | submitted | synced)
- `isrc`, `best_file` (relation → files), `file_count`, `needs_review` (bool)

**`files`** — A concrete audio file on disk:

- `work` (relation → works), `source_dir` (select: yubal | tidal-dl | adhoc)
- `file_path` (unique absolute path), `file_hash` (SHA-256), `acoustid_fp`
- `raw_title`, `raw_artist`, `raw_album` — as found on disk, before cleaning
- `codec`, `sample_rate`, `bit_depth`, `bitrate`, `duration_seconds`
- `quality_score` (0–100), `quality_verdict` (select: authentic | warning | suspicious | fake | lossy)
- `spectral_ceiling` (Hz, from librosa), `is_primary` (bool), `symlink_path`

**`metadata_sources`** — Provenance tracking for every metadata value:

- `file` (relation → files), `source` (select: file_tags | info_json | musicbrainz | discogs | llm | manual)
- `field_name` (text), `value` (text), `confidence` (0–100)

When resolving canonical metadata, the service picks the highest-confidence source per field. Manual edits in the PocketBase UI create a `manual` source entry at `confidence: 100`, overriding everything.

## Quality Scoring Algorithm

Deterministic, signal-based — not LLM-based. Four weighted signals:

| Signal | Weight | Method |
| --- | --- | --- |
| Effective bandwidth | 40% | `librosa.feature.spectral_rolloff` at 99% energy. CD-quality ~22 kHz; 128kbps upscale cuts at ~16 kHz. |
| FLAC Detective | 30% | 11-rule scoring: AUTHENTIC=100, WARNING=75, SUSPICIOUS=25, FAKE_CERTAIN=0. FLAC only; weight redistributed to bandwidth for lossy. |
| Stated format | 20% | 24-bit FLAC=100, 16-bit FLAC=80, 320kbps=50, 256kbps=40, 128kbps=10. |
| Source trust | 10% | tidal-dl=80, adhoc=50, yubal=40. Tiebreaker. |

Files that fail quality checks are not deleted — a 320 kbps upscale may be the only surviving copy of a rare recording. Both versions stay on disk; only the higher-scoring one is symlinked.

## Metadata Confidence Hierarchy

| Source | Confidence | Notes |
| --- | --- | --- |
| Manual edit (PocketBase UI) | 100 | Always final. |
| MusicBrainz (via beets) | 95 | Community-verified gold standard. |
| Discogs (via beets) | 85 | Better South Asian coverage than MB. |
| Tidal/Qobuz file tags | 80 | Commercial tags, usually correct. |
| LLM normalization | 70 | Good for transliteration/genre; unreliable for facts. Pydantic-validated. |
| YouTube / .info.json (Yubal) | 60 | Good title/artist; weak album/genre. |
| Adhoc file tags | 40 | Unknown provenance. |

## beets Configuration

beets is used for MusicBrainz and Discogs matching only (not for file organization — symlinks handle that):

- `quiet_fallback: asis` — unmatched files keep their metadata rather than being skipped
- `data_source_mismatch_penalty: 0.0` for both MB and Discogs
- Preferred countries: `['PK', 'IN', 'US', 'GB']`
- Files without MB matches get `mb_status: pending` for later contribution

Do not convert YouTube audio to FLAC — it gains nothing.

## MusicBrainz Contribution Strategy

The MB API is read-only for entity creation. Contribution is tiered:

1. **Fully automated** (existing MB records): Submit ISRCs via `musicbrainzngs.submit_isrcs()`, AcoustID fingerprints via `pyacoustid`, and genre tags. Headless.
2. **Semi-automated** (existing but unfingerprinted): Submit AcoustID fingerprints for every file with an MBID in its tags.
3. **Seeded browser submission** (new content): Generate seed URLs via `yambs` for the MB release editor. Surface them in PocketBase or via Discord; human reviews and clicks Submit.
4. **LLM normalization before seeding**: Llama 3.1 8B generates ISO 639-3 language codes, ISO 15924 script codes, MB sort names, and edit notes from raw tags.

Weekly n8n workflows: `POST /api/mb/batch-submit` Sunday 3AM → `POST /api/mb/sync` Monday 4AM (24h delay for MB to process submissions).

## Python Compute Service Endpoints

| Endpoint | Method | Returns |
| --- | --- | --- |
| `/api/discover` | POST | `{ new_files, updated_files, skipped, errors }` |
| `/api/analyze` | POST | `{ analyzed, new_works, merged_to_existing, works_changed, needs_review }` |
| `/api/tag` | POST | `{ tagged, mb_matched, llm_cleaned, as_is }` |
| `/api/symlink` | POST | `{ created, updated, removed, plex_scan_triggered }` |
| `/api/mb/batch-submit` | POST | `{ isrcs_submitted, fingerprints_submitted, tags_submitted }` |
| `/api/mb/sync` | POST | `{ synced, new_mbids }` |
| `/api/health` | GET | `{ status, files_total, works_total, broken_symlinks, last_discover, errors }` |
| `/api/work/{id}/reanalyze` | POST | Re-runs quality scoring for a specific work. |
| `/api/work/{id}/seed-url` | GET | Returns MB release editor seed URL. |

The Python service has no database of its own — PocketBase is the single source of truth.

## n8n Workflow Design

**Main pipeline** (every 15 minutes):

```text
[Cron: */15 * * * *]
  → POST /api/discover
    → [IF new_files > 0]
      → POST /api/analyze
        → [IF works_changed > 0] → POST /api/tag → POST /api/symlink → Discord summary
        → [IF needs_review > 0]  → Discord: "N tracks need duplicate review"
```

**MusicBrainz weekly batch**:

```text
[Cron: Sunday 3AM]  → POST /api/mb/batch-submit → Discord summary
[Cron: Monday 4AM]  → POST /api/mb/sync          → Discord summary
```

**Health check** (every 5 minutes):

```text
[Cron: */5 * * * *] → GET /api/health → [IF errors > 0 OR broken_symlinks > 0] → Discord alert
```

**PocketBase realtime hook** (optional): n8n listens for `works` update events via PocketBase SSE. Manual edits in the UI trigger the Python service to re-tag the primary file and re-create the symlink. Plex reflects the change within seconds.

## Notes Directory

- `notes/final-implementation-plan.md` — **Source of truth.** v3 architecture: PocketBase + Python compute + n8n. Full schema, pipeline flow, quality algorithm, roadmap, risk register.
- `notes/claude-revised-plan.md` — v2 architecture (FastAPI + SQLite). Superseded by v3.
- `notes/gemini-revised-plan.md` — Alternative v2 perspective. Superseded by v3.
- `notes/claude-research.md` — Original tool-level research: API calls, config snippets, library comparisons.
- `notes/gemini-research.md` — Original architecture research: distributed design, Windows-as-API strategy, LLM prompt engineering.
