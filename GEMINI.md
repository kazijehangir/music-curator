# Music Curator Pipeline

This project is a self-hosted curation pipeline specializing in Pakistani and South Asian music. It automates the process of ingestion, audio forensics, metadata normalization, and library management.

## 1. Project Overview

### Purpose

* **Metadata Enrichment**: Solving poor MusicBrainz/Discogs coverage for Pakistani music.
* **Audio Forensics**: Detecting "fake FLACs" (upscaled lossy files) using spectral analysis.
* **Standardization**: Resolving transliteration variance and inferring genres using LLMs.
* **Library Management**: Managing a high-quality Plex library using symlinks to preserve original files.

### Core Technology Stack

* **Database & UI**: PocketBase (SQLite-backed, REST API, beautiful Admin UI).
* **Compute Engine**: Python (FastAPI, librosa, pyacoustid, mutagen, beets).
* **Orchestration**: n8n (Visual workflows, cron scheduling, Discord notifications).
* **AI Metadata**: Ollama (Llama 3.1 8B running on Windows for transliteration and normalization).
* **Storage**: Unraid NAS (NFS mounts for media and ingest directories).

## 2. Architecture & Data Model

The system follows a **Three-Layer Architecture** where each component has distinct responsibilities and communicates exclusively via HTTP.

### Data Collections (PocketBase)

* **`music_release`**: Canonical song identities (abstract).
* **`music_file`**: Concrete audio files on disk with forensic metadata.
* **`music_metadata_source`**: Provenance tracking for every metadata value to enable confidence-based selection.

### Pipeline Stages

1. **Discover**: Scan ingest directories (`yubal/`, `tidal-dl/`, `adhoc/`) and index files.
2. **Analyze**: Generate AcoustID fingerprints, calculate quality scores, and deduplicate.
3. **Tag**: Enrich metadata via beets (MB/Discogs), sidecars, and LLM passes.
4. **Symlink**: Link the `best_file` for each release into the Plex library (`/media/Music/`).
5. **Contribute**: Batch submit ISRCs and fingerprints to MusicBrainz.

## 3. Development Conventions

### Source of Truth

* **`notes/final-implementation-plan.md`** is the authoritative architecture document (v3).
* Ignore superseded plans (v1, v2) in the `notes/` directory.

### Key Principles

* **Stateless Compute**: The Python service has no database; it treats PocketBase as the single source of truth.
* **Non-Destructive**: Never delete or modify source audio files (unless tagging metadata in the primary file). Use symlinks for the user-facing library.
* **Signal over Tags**: Trust spectral analysis (`librosa`) over container formats or stated bitrates for quality assessment.
* **Confidence-Based Metadata**: Use the `metadata_sources` hierarchy to resolve conflicts (Manual > MusicBrainz > LLM > Raw Tags).

### Markdown Standards

* **Mandatory Linting**: Every time a Markdown (`.md`) file is created or modified, you MUST run `npx markdownlint-cli --fix <file>` to ensure it adheres to style standards. Fix any remaining warnings manually.

### Technical Environment

* **Python**: Version 3.12+ in a Proxmox LXC.
* **PocketBase**: Running in the same LXC as the Python service (recommended).
* **n8n**: Existing deployment on Proxmox.
* **Ollama**: Running on a Windows machine with GPU, accessed via HTTP.

## 4. Operational Commands (TODO)

* *TODO: Document the command to start the Python FastAPI service once implementation begins.*
* *TODO: Document the PocketBase startup command.*
* *TODO: Document how to run the n8n workflows manually.*

## 5. Key Documentation Files

* `README.md`: High-level summary.
* `CLAUDE.md`: Detailed developer guide for Claude Code.
* `notes/final-implementation-plan.md`: Full architectural specification.
