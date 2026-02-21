# Music Curation Pipeline

Implementation Plan (v3 — Final Architecture)

PocketBase + Python Compute Service + n8n Orchestration
Multi-Source Ingest, Forensic Quality Ranking, Symlink Library
with MusicBrainz Contribution for Pakistani Musical Heritage

Prepared for Jehangir  •  February 2026
Supersedes v1 & v2 — Hybrid PocketBase architecture

## 1. Architecture Evolution

This plan has gone through three iterations of refinement. Here is what changed at each stage and why this v3 represents the final architecture:

| Ver | Architecture | Strength | Weakness |
| :--- | :--- | :--- | :--- |
| **v1** | Custom poller + Huey + Redis. Full pipeline from YTM polling to Plex. | Comprehensive. Detailed audio forensics and MB contribution. | Yubal makes custom poller redundant. Huey replaced by existing n8n. |
| **v2** | FastAPI curation engine + SQLite. Multi-source ingest with symlinks. | Strong data model. Quality scoring algorithm. Symlink design. | Building a web UI from scratch is unnecessary effort. |
| **v3** | PocketBase (DB + UI) + Python compute service + n8n orchestration. | Best of both: zero-code UI, testable Python compute, n8n glue. | Final architecture. Addressed below. |

The v3 principle: each layer does what it's best at. PocketBase owns data storage and the browsing/editing UI. Python owns compute-heavy work (fingerprinting, spectral analysis, beets integration, symlink management). n8n owns scheduling, conditional logic, and notifications. No layer tries to do another layer's job.

## 2. The Three-Layer Architecture

### 2.1 Layer Responsibilities

| Layer | Tool | Responsibility | Why This Tool |
| :--- | :--- | :--- | :--- |
| **Data + UI** | PocketBase | Database schema, REST API, admin UI for browsing/editing catalog, realtime event hooks | Single binary, zero code for UI, SQLite-backed, beautiful admin panel, REST API that n8n and Python both consume |
| **Compute** | Python service (FastAPI) | Audio fingerprinting, spectral analysis, quality scoring, beets/mutagen tag ops, symlink management, MB seed generation | Audio analysis libraries (librosa, pyacoustid, FLAC Detective) are Python-native. Algorithms need testable functions, not n8n Code nodes. |
| **Orchestration** | n8n | Cron scheduling, chaining pipeline stages, conditional branching, Discord notifications, health checks, retries | Already deployed. Visual workflow editor. Execution history for debugging. 400+ integrations for notifications. |
| **GPU (on-demand)** | Ollama via FastAPI on Windows | LLM metadata normalization: transliteration, genre inference, Coke Studio parsing, MB seed data generation | RTX 3080 Ti handles Llama 3.1 8B at Q4_K_M comfortably. HTTP endpoint means any layer can call it. |

### 2.2 How the Layers Communicate

Every interaction between layers is HTTP. No shared state, no file locks, no SSH:

```text
                    ┌──────────────────────────────────┐
                    │       n8n (Orchestrator)      │
                    │  Cron triggers, conditionals, │
                    │  retries, Discord webhooks    │
                    └────────┬───────────────┬─────────┘
             HTTP POST │               │ HTTP GET/POST
        (trigger stage) │               │ (read/write DB)
                    ┌───┴───────┐   ┌───┴─────────┐
                    │  Python   │   │  PocketBase  │
                    │  Compute  ├───┤  (DB + UI)   │
                    │  Service  │   │  :8090       │
                    └────┬──────┘   └─────────────┘
                 HTTP │ (LLM calls)
                    ┌──┴──────────┐
                    │  Windows PC   │
                    │  Ollama :5000  │
                    └─────────────┘
```

* All layers read/write files on Unraid NAS via NFS mounts.
* PocketBase stores metadata. Files stay on NAS. Symlinks in `/media/Music/`.

### 2.3 Infrastructure Topology

| Node | Role | Services |
| :--- | :--- | :--- |
| **Proxmox LXC #1** | Curation Engine | Python FastAPI service (compute endpoints), PocketBase (DB + admin UI). Both run here. 2 cores, 2 GB RAM, 20 GB disk. |
| **Proxmox (existing)** | n8n | Already deployed. Triggers compute endpoints on schedule. Reads/writes PocketBase. Sends Discord notifications. |
| **Windows PC** | GPU API | Ollama + Llama 3.1 8B via FastAPI on port 5000. Called by the Python compute service only when LLM cleaning is needed. |
| **Unraid NAS** | Storage + Plex | Hosts the three ingest dirs, the symlink library at `/media/Music/`, and Plex Media Server. Yubal runs here writing to `yubal/`. |

### 2.4 Directory Layout

```text
/mnt/user/main/downloads/unseeded/music/
├── yubal/              # Yubal writes here continuously
│   ├── Artist Name/
│   │   ├── Album/
│   │   │   ├── 01 - Track.opus
│   │   │   └── 01 - Track.info.json
├── tidal-dl/           # Bulk Tidal/Qobuz FLAC downloads
│   ├── Artist Name/
│   │   ├── Album/
│   │   │   ├── 01 - Track.flac
├── adhoc/              # Manual one-off drops, any structure

/mnt/user/main/media/Music/          # PLEX LIBRARY (symlinks only)
├── Artist Name/
│   ├── Album/
│   │   ├── 01 - Track.flac  → ../../../downloads/.../Track.flac
```

## 3. PocketBase Database Schema

PocketBase uses "collections" (equivalent to tables). The schema has three collections that model the core data relationships. The key improvement over the simpler two-table schema proposed elsewhere: the `music_metadata_source` collection tracks provenance, so you can always see which source provided which metadata value and at what confidence level.

### 3.1 Collection: music_release

A "release" (formerly work) is an abstract song identity — "Pasoori" by Ali Sethi & Shae Gill, regardless of how many files you have of it:

| Field | Type | Description |
| :--- | :--- | :--- |
| `canonical_title` | text | Best-known title, after LLM normalization |
| `canonical_artist` | text | Best-known artist name |
| `canonical_album` | text | Album name (may be empty for YouTube singles) |
| `genre` | text | Specific genre: Qawwali, Ghazal, Pakistani Pop, etc. |
| `language` | text | ISO 639-3 code (urd, pan, hin, eng) |
| `mb_recording_id` | text | MusicBrainz Recording MBID (if matched) |
| `mb_release_id` | text | MusicBrainz Release MBID |
| `mb_status` | select | unknown \| matched \| pending \| submitted \| synced |
| `isrc` | text | ISRC if found in any file's tags |
| `best_file` | relation → music_file | Points to the highest-quality file (the symlinked version) |
| `file_count` | number | How many versions exist (denormalized for quick display) |
| `needs_review` | bool | True if fuzzy-matched files need human confirmation |

### 3.2 Collection: music_file

A "file" is a concrete audio file on disk, linked to a release:

| Field | Type | Description |
| :--- | :--- | :--- |
| `release` | relation → music_release | Which abstract song this file belongs to |
| `source_dir` | text | Source directory name (yubal, tidal-dl, adhoc) |
| `file_path` | text (unique) | Absolute path on NAS |
| `file_hash` | text | SHA-256 of file content (for change detection) |
| `acoustid_fp` | text | Chromaprint fingerprint (for deduplication) |
| `raw_title__raw_artist__raw_album` | text | Combined metadata found on disk before cleaning |
| `codec` | text | flac, opus, aac, mp3 |
| `sample_rate` | number | 44100, 48000, 96000 Hz |
| `bit_depth` | number | 16, 24, or null for lossy codecs |
| `bitrate` | number | kbps (stated bitrate) |
| `duration_seconds` | number | Track duration |
| `quality_score` | number | 0–100 composite score (see Section 5) |
| `quality_verdict` | select | authentic \| warning \| suspicious \| fake \| lossy |
| `spectral_ceiling` | number | Effective frequency ceiling in Hz (from librosa) |
| `is_primary` | bool | True if this is the currently symlinked version |
| `symlink_path` | text | Path in `/media/Music/` (if this file is primary) |

### 3.3 Collection: music_metadata_source

This is the collection that tracks the provenance of metadata. When the same track comes from multiple sources, each provides different values.

| Field | Type | Description |
| :--- | :--- | :--- |
| `file` | relation → music_file | Which file this metadata came from |
| `source` | select | file_tags \| info_json \| musicbrainz \| discogs \| llm \| manual |
| `field_name` | text | Which metadata field: title, artist, album, genre, year, etc. |
| `value` | text | The metadata value from this source |
| `confidence` | number | 0–100, based on source trust hierarchy (see Section 7) |

When the Python service resolves the canonical metadata for a `music_release`, it queries `music_metadata_source` for all field values across all files in that group, picks the highest-confidence value for each field, and writes the result to the release's canonical fields.

## 4. Pipeline Flow

The pipeline is five stages, triggered by n8n on a 15-minute cron cycle. Each stage is an HTTP call from n8n to the Python compute service, which reads/writes PocketBase:

### 4.1 Stage 1: Discover

n8n calls: `POST /api/discover`
The Python service walks all three ingest directories and checks each file against PocketBase. New files (hash not in DB) get inserted into the `music_file` collection with raw metadata.

```python
# Pseudocode for the discovery scanner

for dir in ['yubal', 'tidal-dl', 'adhoc']:
    for path in walk_audio_files(INGEST_ROOT / dir):
        file_hash = sha256(path)
        existing = pb.collection('music_file').get_list(
            filter=f'file_path="{path}"')
        if not existing.items:
            # New file: extract metadata, insert
            meta = extract_metadata(path)  # mutagen
            pb.collection('music_file').create({
                'source_dir': dir,
                'file_path': str(path),
                'file_hash': file_hash,
                'raw_title__raw_artist__raw_album': f"{meta['title']} | {meta['artist']} | {meta['album']}",
                'codec': meta['codec'],
                'sample_rate': meta['sample_rate'],
                # ... etc
            })
            new_count += 1
        elif existing.items[0].file_hash != file_hash:
            # File changed: re-queue for analysis
            pb.collection('music_file').update(existing.items[0].id, {
                'file_hash': file_hash,
                'quality_score': None,  # reset
            })
```

### 4.2 Stage 2: Analyze (Fingerprint + Quality + Dedup)

n8n calls: `POST /api/analyze`
This is the heaviest stage. For each unanalyzed file in PocketBase, the service:

1. Generates AcoustID fingerprint via `fpcalc/pyacoustid` and stores it in the `music_file` record.
2. Runs quality scoring (see Section 5) using FLAC Detective + librosa spectral rolloff.
3. Attempts deduplication: searches existing files in PocketBase for fingerprint matches or fuzzy metadata matches.

The dedup outcome determines the next action:

* **Strong fingerprint match:** auto-group the file under the existing `music_release`.
* **Fuzzy metadata match only:** create the grouping but set `needs_review = true` on the `music_release`.
* **No match:** create a new `music_release` with canonical fields populated from the file's raw metadata.

After grouping, the service re-evaluates the `best_file` for each affected release by comparing `quality_score`.

### 4.3 Stage 3: Tag + Enrich

n8n calls: `POST /api/tag`
For releases where the primary file has changed or the release is newly created, the service runs a three-pass metadata enrichment:

* **Pass 1 — beets auto-match:** Run `beet import -q`. If matched, store MBID in `music_release` and insert `music_metadata_source` entries with `source: musicbrainz`.
* **Pass 2 — mutagen gap-fill:** For missing fields, read from `.info.json` sidecars and from other file tags in the same release group.
* **Pass 3 — LLM normalization:** For unmatched releases, send raw metadata to Ollama on Windows for transliteration and genre inference.

The service then resolves canonical metadata from `music_metadata_source` and writes clean tags into the primary file via mutagen.

### 4.4 Stage 4: Symlink + Serve

n8n calls: `POST /api/symlink`
For every release where the primary file has changed, the service:

1. Removes the old symlink (if one exists) from `/media/Music/`
2. Constructs the new Plex-compatible path based on canonical metadata.
3. Creates the new symlink pointing to the primary file's location.
4. Updates the `symlink_path` field in `music_file`.
5. Triggers a Plex library scan.

### 4.5 Stage 5: MusicBrainz Contribution (Weekly Batch)

n8n calls: `POST /api/mb/batch-submit` (weekly) and `POST /api/mb/sync` (weekly, 24h later)

* **Automated (no human):** Submit ISRCs and fingerprints for works with `mb_status: matched`.
* **Seeded (one click per release):** For works with `mb_status: pending`, generate seed URLs using `yambs`. Surface these in PocketBase's UI.
* **Feedback loop:** Run `beet mbsync` weekly to pull new MBIDs.

## 5. Quality Scoring Algorithm

The scoring system analyzes the actual audio signal to catch upscales.

### 5.1 Four Signals, Weighted

| Signal | Weight | Method |
| :--- | :--- | :--- |
| **Effective bandwidth** | 40% | `librosa.feature.spectral_rolloff` analysis. |
| **FLAC Detective** | 30% | 11-rule scoring for FLAC authenticity. |
| **Stated format** | 20% | Bit depth and bitrate stated by the file. |
| **Source trust** | 10% | tidal-dl > adhoc > yubal. |

### 5.2 How This Catches the Tidal Upscale Problem

| Signal | Tidal FLAC (fake) | YouTube Opus (genuine) |
| :--- | :--- | :--- |
| **Spectral ceiling** | 16.2 kHz | 20.0 kHz |
| **COMPOSITE SCORE** | **46.3 — verdict: fake** | **70.6 — verdict: authentic (lossy)** |

The Opus file wins and gets symlinked.

## 6. n8n Workflow Design

### 6.1 The Main Pipeline Workflow

Runs every 15 minutes:
`[Cron: */15 * * * *]`
  → `[HTTP POST: python-service:8000/api/discover]`
    → `[IF: new_files > 0]`
      → `[HTTP POST: python-service:8000/api/analyze]`
        → `[IF: changed > 0]`
          → `[HTTP POST: python-service:8000/api/tag]`
            → `[HTTP POST: python-service:8000/api/symlink]`
              → `[Discord: summary]`

### 6.2 MusicBrainz Weekly Batch

`[Cron: Sunday 3AM]` → `[HTTP POST: /api/mb/batch-submit]`
`[Cron: Monday 4AM]` → `[HTTP POST: /api/mb/sync]`

### 6.3 PocketBase Realtime Hook

Manually editing `music_release` in the UI triggers n8n via SSE, which tells the Python service to: (a) create a `manual` source entry, (b) re-tag the file, and (c) update the symlink.

## 7. Metadata Confidence Hierarchy

| Source | Confidence | Notes |
| :--- | :--- | :--- |
| **Manual edit (PocketBase UI)** | 100 | Always final. |
| **MusicBrainz (via beets)** | 95 | The gold standard. |
| **Tidal/Qobuz file tags** | 80 | Commercial tags. |
| **LLM normalization** | 70 | Transliteration and genre. |
| **YouTube / .info.json (Yubal)** | 60 | User-uploaded metadata. |

## 8. Python Compute Service API Reference

| Endpoint | Method | Returns |
| :--- | :--- | :--- |
| `/api/discover` | POST | `{ new_files: N, ... }` |
| `/api/analyze` | POST | `{ analyzed: N, new_releases: N, ... }` |
| `/api/tag` | POST | `{ tagged: N, mb_matched: N, ... }` |
| `/api/symlink` | POST | `{ created: N, plex_scan_triggered: bool }` |
| `/api/mb/batch-submit` | POST | `{ isrcs_submitted: N, ... }` |
| `/api/mb/sync` | POST | `{ synced: N, new_mbids: N }` |
| `/api/health` | GET | `{ status: ok, broken_symlinks: N, ... }` |
| `/api/release/{id}/reanalyze` | POST | Manual trigger for a specific release. |

## 9. What You See in PocketBase

### 9.1 Browsing Your Catalog

Open the `music_release` collection to see your canonical library.

### 9.2 Inspecting a Release

Click a release record. Filter `music_file` by `release = [ID]` to see all versions and their quality scores.

### 9.3 Editing Metadata

Edits in `music_release` are instantly reflected in Plex via realtime hooks.

## 10. Implementation Roadmap

### Phase 1: PocketBase + Discovery (Days 1–6)

* **Day 1–2:** Deploy PocketBase. Create `music_release`, `music_file`, `music_metadata_source`.
* **Day 3–6:** Provision LXC. Write `/api/discover`.

### Phase 2: Fingerprinting + Quality + Dedup (Days 7–14)

* **Day 7–14:** Implement fingerprinting and quality scoring. Wire up `/api/analyze`.

### Phase 3: Symlinks + Plex (Days 15–19)

* **Day 15–19:** Symlink manager + Plex scan trigger.

### Phase 4: Metadata Intelligence (Days 20–26)

* **Day 20–26:** Beets integration + Ollama LLM normalization.

### Phase 5: MusicBrainz Contribution (Days 27–32)

* **Day 27–32:** Batch submission and MBID syncing.

### Phase 6: Polish (Days 33–35)

* **Day 33–35:** Realtime hooks and health checks.

## 11. Full Technology Stack

| Layer | Tool | Why |
| :--- | :--- | :--- |
| **YouTube Music sync** | Yubal | Writes to `yubal/` directory. |
| **Orchestration** | n8n | Scheduling, logic, Discord. |
| **Database + UI** | PocketBase | DB schema, REST API, Admin UI. |
| **Compute service** | Python + FastAPI | Audio analysis, tagging, symlinks. |
| **Audio fingerprinting** | `pyacoustid` | Deduplication and MB contribution. |
| **Quality analysis** | `librosa` | Upscale detection. |
| **Metadata tagging** | beets + mutagen | Matching and tag R/W. |
| **LLM metadata** | Ollama | Transliteration and genre inference. |

## 12. Maintenance CLI Commands

The Python compute service ships a CLI for one-off operational tasks that are not part of the regular n8n pipeline.

| Command | Description |
| :--- | :--- |
| `python -m src.cli discover` | Run file discovery manually. |
| `python -m src.cli analyze` | Run audio analysis / fingerprinting manually. |
| `python -m src.cli cleanup-releases` | Delete `music_release` rows that have no `music_file` pointing to them. Safe to re-run; prints a progress count and a final summary. |
| `python -m src.cli repair-metadata` | Re-extract tags for `music_file` records stored with empty metadata (`' \| \| '`). Targets files whose tag format was not recognized at discovery time (e.g. M4A files using `©nam`/`©ART`/`©alb` MP4 keys). Safe to re-run. |

## 13. Risk Register

| Risk | Severity | Mitigation |
| :--- | :--- | :--- |
| **PocketBase SQLite lock** | Med | Sequential pipeline stages via n8n. |
| **Broken symlinks** | Med | Health check endpoint monitors resolution. |
| **Plex symlink support** | High | Correct volume mounts in Docker. |
| **LLM hallucination** | Med | Confidence capping and Pydantic validation. |
| **Duplicate `music_release` rows** | Med | Fixed: analyze filter no longer uses PocketBase's `!~` (substring) operator as a regex; existing release assignment is preserved on re-analysis. Run `cleanup-releases` CLI command to purge any orphans already in the database. |
| **Missing metadata for M4A files** | Low | Fixed: `extract_metadata` now reads MP4 atom keys (`©nam`/`©ART`/`©alb`) in addition to Vorbis Comment and ID3 keys. Run `repair-metadata` CLI command to back-fill records already in the database. |

## 14. Open Decisions

* **PocketBase deployment:** Same LXC as Python for fastest performance.
* **Custom frontend:** Admin UI is sufficient for Phase 1.
* **Cover art:** Beets fetchart for matched tracks; Yubal thumbnails for unmatched.
