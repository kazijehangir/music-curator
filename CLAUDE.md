# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a self-hosted music curation pipeline focused on Pakistani/South Asian music. The core challenge is that tools like Lidarr and MusicBrainz Picard assume good MusicBrainz coverage, which doesn't exist for this genre. The pipeline must handle transliteration variance, upscaled lossy files masquerading as FLAC, and singleton releases (singles released directly to YouTube/SoundCloud that have no MusicBrainz entry).

The project is currently in the **research/planning phase**. `notes/` contains two research documents (from Claude and Gemini) that represent the source of truth for architectural decisions.

## Hardware Topology

| Node | Role | Key Services |
|---|---|---|
| Proxmox LXC | Orchestration | Python orchestrator, SQLite state DB, Huey/n8n scheduler |
| Unraid | Storage | beets (Docker), Plex, NFS exports for `/ingest` and `/library` |
| Windows PC (RTX 3080 Ti) | GPU Compute | Ollama (Llama 3.1 8B), audio forensics, exposed via FastAPI |
| MacBook | Verification | Human-in-the-loop MusicBrainz submission review |

The Windows machine is treated as an on-demand compute API rather than a script runner — the Proxmox orchestrator sends HTTP POST requests to a FastAPI endpoint on Windows for GPU-heavy tasks (LLM inference, spectrogram analysis).

## Pipeline Architecture

Five stages, each with a primary tool and fallback:

```
Poll (ytmusicapi) → Download (streamrip → yt-dlp fallback) → Tag (beets → mutagen)
    → Organize (beets paths → Unraid NAS) → Serve (Plex/Plexamp)
```

**Stage 1 — Poll:** ytmusicapi `get_liked_songs(limit=None)` every 30 minutes via Huey periodic task. State tracked in SQLite (`tracked_songs` table keyed on `videoId`). No webhooks exist; polling is the only option. Use ytmusicapi, **not** the official YouTube Data API v3 (wrong playlist ID, quota limits, no YTM-specific metadata).

**Stage 2 — Download:** Search Qobuz → Tidal → Deezer via streamrip for lossless. Fall back to yt-dlp from YouTube Music (max 256 kbps AAC, format `141` preferred over `774`). Always write `.info.json` sidecars. Converting YouTube audio to FLAC gains nothing — don't do it.

**Stage 3 — Tag:** `beet import -q` with `quiet_fallback: asis` so unmatched files keep YouTube metadata rather than being skipped. Post-process with mutagen to fill gaps from `.info.json`. LLM QA pass via Ollama flags missing fields, mojibake, and inconsistent transliteration.

**Stage 4 — Organize:** beets moves files to `$albumartist/$album/$disc$track $title` on the NAS mount, triggers Plex scan via `plexupdate` plugin.

**Stage 5 — Serve:** Plexamp with sonic analysis enabled (requires Plex Pass, x86 CPU).

## Key Architectural Decisions

**Audio quality verification** uses deterministic tools, not LLMs: FLAC Detective (`pip install flac-detective`) for classification, `librosa.feature.spectral_rolloff` for cutoff detection, SoX/ffmpeg for spectrograms. Files that fail go to a `_Review/Upscales` folder with a Discord/Telegram notification — they are never deleted because a 320 kbps upscale may be the only surviving copy of a rare recording.

**Deduplication before downloading** uses a multi-layer approach: beets DB query → PlexAPI fallback → fuzzy matching with `thefuzz` (`token_sort_ratio > 85` for title AND `> 90` for artist triggers a "Manual Review" flag rather than auto-skip).

**beets is configured for South Asian music** with `data_source_mismatch_penalty: 0.0` for both MusicBrainz and Discogs (Discogs has better South Asian coverage), `quiet_fallback: asis`, and preferred countries `['PK', 'IN', 'US', 'GB']`. Files without MusicBrainz matches get a custom field `mb_status: pending` for later contribution.

## MusicBrainz Contribution Strategy

The MusicBrainz API is read-only for entity creation. Contribution is tiered:

1. **Fully automated** (existing MB records): Submit ISRCs via `musicbrainzngs.submit_isrcs()`, barcodes, and genre tags. All headless.
2. **Semi-automated** (existing but unfingerprinted): Submit AcoustID fingerprints via `pyacoustid` for every file with an MBID in its tags.
3. **Seeded browser submission** (new content): Generate POST bodies for `musicbrainz.org/release/add` pre-filling the release editor. A local Flask/FastAPI "pending submissions" queue lets you batch these — one click opens the pre-filled form, human reviews and clicks Submit. Tool: [yambs](https://codeberg.org/derat/yambs).
4. **LLM normalization** before seeding: Llama 3.1 8B generates correct ISO 639-3 language codes, ISO 15924 script codes, MB-format sort names, and edit notes from raw FLAC tags.

After submission, `beet mbsync` runs on a 24-hour delay to pick up the new MBIDs and update local tags.

## Storage Layout

```
/mnt/user/data/ingest/       — Raw streamrip/yt-dlp downloads
/mnt/user/data/processing/   — Files during forensic analysis and tagging
/mnt/user/media/music/       — Final Plex-ready library (beets-managed)
```

## Orchestration Choice

**Huey + Redis** is the recommended minimal orchestrator (~50 MB RAM, Python-native, built-in retry). **n8n** (Docker, ~300 MB RAM) is preferred if visual pipeline monitoring matters. Avoid Airflow, Dagster, and Celery — all overkill. Plain cron works for zero-dependency deployments but requires manual retry/logging implementation.

## Notes Directory

- `notes/claude-research.md` — Detailed tool-level research: specific API calls, config snippets, library comparisons, and the MusicBrainz contribution tiers
- `notes/gemini-research.md` — Architecture-level research: distributed microservices design, the "Windows-as-API" strategy, LLM prompt engineering for South Asian metadata, and the full 30-day implementation roadmap