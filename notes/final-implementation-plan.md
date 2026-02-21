# Music Curation Pipeline

Implementation Plan (v3 — Final Architecture)

PocketBase + Python Compute Service + n8n Orchestration
Multi-Source Ingest, Forensic Quality Ranking, Symlink Library
with MusicBrainz Contribution for Pakistani Musical Heritage

Prepared for Jehangir  •  February 2026
Supersedes v1 & v2 — Hybrid PocketBase architecture

1. Architecture Evolution
This plan has gone through three iterations of refinement. Here is what changed at each stage and why this v3 represents the final architecture:

Ver
Architecture
Strength
Weakness
v1
Custom poller + Huey + Redis. Full pipeline from YTM polling to Plex.
Comprehensive. Detailed audio forensics and MB contribution.
Yubal makes custom poller redundant. Huey replaced by existing n8n.
v2
FastAPI curation engine + SQLite. Multi-source ingest with symlinks.
Strong data model. Quality scoring algorithm. Symlink design.
Building a web UI from scratch is unnecessary effort.
v3
PocketBase (DB + UI) + Python compute service + n8n orchestration.
Best of both: zero-code UI, testable Python compute, n8n glue.
Final architecture. Addressed below.

The v3 principle: each layer does what it's best at. PocketBase owns data storage and the browsing/editing UI. Python owns compute-heavy work (fingerprinting, spectral analysis, beets integration, symlink management). n8n owns scheduling, conditional logic, and notifications. No layer tries to do another layer's job.

1. The Three-Layer Architecture
2.1 Layer Responsibilities

Layer
Tool
Responsibility
Why This Tool
Data + UI
PocketBase
Database schema, REST API, admin UI for browsing/editing catalog, realtime event hooks
Single binary, zero code for UI, SQLite-backed, beautiful admin panel, REST API that n8n and Python both consume
Compute
Python service (FastAPI)
Audio fingerprinting, spectral analysis, quality scoring, beets/mutagen tag ops, symlink management, MB seed generation
Audio analysis libraries (librosa, pyacoustid, FLAC Detective) are Python-native. Algorithms need testable functions, not n8n Code nodes.
Orchestration
n8n
Cron scheduling, chaining pipeline stages, conditional branching, Discord notifications, health checks, retries
Already deployed. Visual workflow editor. Execution history for debugging. 400+ integrations for notifications.
GPU (on-demand)
Ollama via FastAPI on Windows
LLM metadata normalization: transliteration, genre inference, Coke Studio parsing, MB seed data generation
RTX 3080 Ti handles Llama 3.1 8B at Q4_K_M comfortably. HTTP endpoint means any layer can call it.

2.2 How the Layers Communicate
Every interaction between layers is HTTP. No shared state, no file locks, no SSH:
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

  All layers read/write files on Unraid NAS via NFS mounts.
  PocketBase stores metadata. Files stay on NAS. Symlinks in /media/Music/.
2.3 Infrastructure Topology

Node
Role
Services
Proxmox LXC #1
Curation Engine
Python FastAPI service (compute endpoints), PocketBase (DB + admin UI). Both run here. 2 cores, 2 GB RAM, 20 GB disk.
Proxmox (existing)
n8n
Already deployed. Triggers compute endpoints on schedule. Reads/writes PocketBase. Sends Discord notifications.
Windows PC
GPU API
Ollama + Llama 3.1 8B via FastAPI on port 5000. Called by the Python compute service only when LLM cleaning is needed.
Unraid NAS
Storage + Plex
Hosts the three ingest dirs, the symlink library at /media/Music/, and Plex Media Server. Yubal runs here writing to yubal/.

2.4 Directory Layout
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

1. PocketBase Database Schema
PocketBase uses "collections" (equivalent to tables). The schema has three collections that model the core data relationships. The key improvement over the simpler two-table schema proposed elsewhere: the metadata_sources collection tracks provenance, so you can always see which source provided which metadata value and at what confidence level.
3.1 Collection: works
A "work" is an abstract song identity — "Pasoori" by Ali Sethi & Shae Gill, regardless of how many files you have of it:

Field
Type
Description
canonical_title
text
Best-known title, after LLM normalization
canonical_artist
text
Best-known artist name
canonical_album
text
Album name (may be empty for YouTube singles)
genre
text
Specific genre: Qawwali, Ghazal, Pakistani Pop, etc.
language
text
ISO 639-3 code (urd, pan, hin, eng)
mb_recording_id
text
MusicBrainz Recording MBID (if matched)
mb_release_id
text
MusicBrainz Release MBID
mb_status
select
unknown | matched | pending | submitted | synced
isrc
text
ISRC if found in any file's tags
best_file
relation → files
Points to the highest-quality file (the symlinked version)
file_count
number
How many versions exist (denormalized for quick display)
needs_review
bool
True if fuzzy-matched files need human confirmation

3.2 Collection: files
A "file" is a concrete audio file on disk, linked to a work:

Field
Type
Description
work
relation → works
Which abstract song this file belongs to
source_dir
select
yubal | tidal-dl | adhoc
file_path
text (unique)
Absolute path on NAS, e.g. /mnt/user/main/downloads/unseeded/music/tidal-dl/Artist/Album/Track.flac
file_hash
text
SHA-256 of file content (for change detection)
acoustid_fp
text
Chromaprint fingerprint (for deduplication)
raw_title / raw_artist / raw_album
text
Metadata as found on disk, before any cleaning
codec
text
flac, opus, aac, mp3
sample_rate
number
44100, 48000, 96000 Hz
bit_depth
number
16, 24, or null for lossy codecs
bitrate
number
kbps (stated bitrate)
duration_seconds
number
Track duration
quality_score
number
0–100 composite score (see Section 5)
quality_verdict
select
authentic | warning | suspicious | fake | lossy
spectral_ceiling
number
Effective frequency ceiling in Hz (from librosa)
is_primary
bool
True if this is the currently symlinked version
symlink_path
text
Path in /media/Music/ (if this file is primary)

3.3 Collection: metadata_sources
This is the collection the other proposal missed. When the same track comes from YouTube, Tidal, and the LLM, each provides different metadata. By tracking the provenance of every field value, the system can pick the highest-confidence value and you can see in the UI why a particular title or artist name was chosen.

Field
Type
Description
file
relation → files
Which file this metadata came from
source
select
file_tags | info_json | musicbrainz | discogs | llm | manual
field_name
text
Which metadata field: title, artist, album, genre, year, etc.
value
text
The metadata value from this source
confidence
number
0–100, based on source trust hierarchy (see Section 7)

When the Python service resolves the canonical metadata for a work, it queries metadata_sources for all field values across all files in that work group, picks the highest-confidence value for each field, and writes the result to the work's canonical fields. If you manually edit a field in PocketBase, a manual source entry is created with confidence 100, which overrides everything.

1. Pipeline Flow
The pipeline is five stages, triggered by n8n on a 15-minute cron cycle. Each stage is an HTTP call from n8n to the Python compute service, which reads/writes PocketBase:
4.1 Stage 1: Discover
n8n calls: POST /api/discover
The Python service walks all three ingest directories, computes SHA-256 hashes, and checks each file against PocketBase. New files (hash not in DB) get inserted into the files collection with raw metadata extracted via mutagen. Changed files (path exists but hash differs) get re-queued for analysis. For Yubal files, the service also reads .info.json sidecars and stores the YouTube metadata.

# Pseudocode for the discovery scanner

for dir in ['yubal', 'tidal-dl', 'adhoc']:
    for path in walk_audio_files(INGEST_ROOT / dir):
        file_hash = sha256(path)
        existing = pb.collection('files').get_list(
            filter=f'file_path="{path}"')
        if not existing.items:
            # New file: extract metadata, insert
            meta = extract_metadata(path)  # mutagen
            pb.collection('files').create({
                'source_dir': dir,
                'file_path': str(path),
                'file_hash': file_hash,
                'raw_title': meta['title'],
                'raw_artist': meta['artist'],
                'codec': meta['codec'],
                'sample_rate': meta['sample_rate'],
                # ... etc
            })
            new_count += 1
        elif existing.items[0].file_hash != file_hash:
            # File changed: re-queue for analysis
            pb.collection('files').update(existing.items[0].id, {
                'file_hash': file_hash,
                'quality_score': None,  # reset
            })
4.2 Stage 2: Analyze (Fingerprint + Quality + Dedup)
n8n calls: POST /api/analyze
This is the heaviest stage. For each unanalyzed file in PocketBase, the service:
Generates AcoustID fingerprint via fpcalc/pyacoustid and stores it in the file record.
Runs quality scoring (see Section 5) using FLAC Detective + librosa spectral rolloff. Stores quality_score, quality_verdict, and spectral_ceiling.
Attempts deduplication: searches existing files in PocketBase for fingerprint matches (correlation > 0.85) or fuzzy metadata matches (thefuzz token_sort_ratio > 85 for title, > 90 for artist, duration within 10 seconds).
The dedup outcome determines the next action:
Strong fingerprint match: auto-group the file under the existing work. No human review needed.
Fuzzy metadata match only: create the grouping but set needs_review = true on the work. This appears in the PocketBase UI for human confirmation.
No match: create a new work with canonical fields populated from the file's raw metadata.
After grouping, the service re-evaluates the best_file for each affected work by comparing quality_score across all files in the group. If the new file beats the current primary, the best_file relation is updated and is_primary flags are swapped.
4.3 Stage 3: Tag + Enrich
n8n calls: POST /api/tag
For works where the primary file has changed or the work is newly created, the service runs a three-pass metadata enrichment:
Pass 1 — beets auto-match: Run beet import -q against MusicBrainz and Discogs with quiet_fallback: asis. If a match is found (confidence ≥ 0.80), store the MBID in the work and insert metadata_sources entries with source: musicbrainz and confidence: 95.
Pass 2 — mutagen gap-fill: For fields that beets didn't populate, read from .info.json sidecars (confidence: 60) and from file tags across all versions of the work (confidence varies by source_dir: 80 for tidal-dl, 60 for yubal, 40 for adhoc).
Pass 3 — LLM normalization: For works that remain unmatched in MusicBrainz, send raw metadata to the Ollama endpoint on Windows for transliteration standardization, genre inference, and Coke Studio parsing. Store results with source: llm and confidence: 70.
The service then resolves canonical metadata by selecting the highest-confidence value for each field from metadata_sources and writing it to the work record. It also writes the clean tags into the primary file via mutagen, so the actual audio file has correct embedded metadata.
4.4 Stage 4: Symlink + Serve
n8n calls: POST /api/symlink
For every work where the primary file has changed, the service:
Removes the old symlink (if one exists) from /media/Music/
Constructs the new Plex-compatible path: /media/Music/{canonical_artist}/{canonical_album or 'Singles'}/{canonical_title}.{ext}
Creates the new symlink pointing to the primary file's location in the ingest directory
Updates the symlink_path field in PocketBase
Triggers a Plex library scan via the Plex API (using plexapi Python library or a direct HTTP call to Plex)
Plex volume mount requirement: Plex's Docker container on Unraid must have both /media/Music and /downloads/unseeded/music mounted as volumes so it can follow the symlinks. Both must be accessible under the same paths the symlinks use, or the symlinks will resolve to broken paths inside the container.
4.5 Stage 5: MusicBrainz Contribution (Weekly Batch)
n8n calls: POST /api/mb/batch-submit (weekly) and POST /api/mb/sync (weekly, 24h later)
The MB contribution pipeline from v2 remains unchanged in this architecture:
Automated (no human): Submit ISRCs, AcoustID fingerprints, and genre tags for all works with mb_status: matched via musicbrainzngs.
Seeded (one click per release): For works with mb_status: pending, generate seed URLs using yambs. Surface these in PocketBase's UI with a custom field or as a separate "mb_submissions" collection that you can browse and click through.
Feedback loop: Run beet mbsync weekly to pull new MBIDs for recently submitted releases. Update mb_status to synced.

1. Quality Scoring Algorithm
The scoring system is the same composite algorithm from v2, reproduced here for completeness. The key insight: it analyzes the actual audio signal, not just the file format or bitrate. This is what catches the Tidal upscale fraud you identified with Fakin’ the Funk.
5.1 Four Signals, Weighted

Signal
Weight
Method
Effective bandwidth
40%
librosa.feature.spectral_rolloff at 99% energy. CD-quality reaches ~22 kHz. A 128kbps upscale cuts at ~16 kHz. A 320kbps upscale cuts at ~19–20 kHz.
FLAC Detective
30%
11-rule scoring: AUTHENTIC=100, WARNING=75, SUSPICIOUS=25, FAKE_CERTAIN=0. Only for FLAC files; weight redistributed to bandwidth for lossy.
Stated format
20%
24-bit FLAC=100, 16-bit FLAC=80, 320kbps lossy=50, 256kbps lossy=40, 128kbps lossy=10.
Source trust
10%
tidal-dl=80, adhoc=50, yubal=40. Tiebreaker when spectral evidence is equivalent.

5.2 How This Catches the Tidal Upscale Problem
Concrete example with two versions of the same track:

Signal
Tidal FLAC (fake)
YouTube Opus (genuine)
Spectral ceiling
16.2 kHz (content stops at MP3 boundary)
20.0 kHz (genuine 256kbps encoding)
Bandwidth score
37 (16200/22050 × 110, capped)
91 (20000/22050 × 110, capped at 100)
FLAC Detective
SUSPICIOUS = 25
N/A (lossy, weight redistributed)
Stated format
80 (16-bit FLAC)
40 (256kbps lossy)
Source trust
80 (tidal-dl)
40 (yubal)
COMPOSITE SCORE
46.3 — verdict: fake
70.6 — verdict: authentic (lossy)

The Opus file wins and gets symlinked. The Tidal FLAC stays on disk but is not served to Plex. Both are visible in PocketBase's UI under the same work, with full quality details, so you can override the decision if needed.

1. n8n Workflow Design
6.1 The Main Pipeline Workflow
This is the primary workflow that runs every 15 minutes:
[Cron: */15* ** *]
  → [HTTP POST: python-service:8000/api/discover]
    → [IF: result.new_files > 0]
      → [HTTP POST: python-service:8000/api/analyze]
        → [IF: result.works_changed > 0]
          → [HTTP POST: python-service:8000/api/tag]
            → [HTTP POST: python-service:8000/api/symlink]
              → [Discord Webhook: summary]
        → [IF: result.needs_review > 0]
          → [Discord Webhook: "N tracks need duplicate review"]
6.2 MusicBrainz Weekly Batch
[Cron: Sunday 3AM]
  → [HTTP POST: python-service:8000/api/mb/batch-submit]
    → [Discord: "Submitted N ISRCs, N fingerprints, N tags"]

[Cron: Monday 4AM]
  → [HTTP POST: python-service:8000/api/mb/sync]
    → [Discord: "Synced N new MBIDs from MusicBrainz"]
6.3 PocketBase Realtime Hook (Optional But Powerful)
PocketBase supports realtime event hooks. You can configure n8n to listen for update events on the works collection via PocketBase's SSE (Server-Sent Events) endpoint. When you manually edit a canonical_title or canonical_artist in the PocketBase UI, n8n detects the change and triggers the Python service to: (a) write a metadata_sources entry with source: manual and confidence: 100, (b) re-tag the primary file via mutagen, and (c) re-create the symlink with the new naming. This means edits you make in the PocketBase UI are instantly reflected in your Plex library.
6.4 Health Check
[Cron: */5* ** *]
  → [HTTP GET: python-service:8000/api/health]
    → [IF: errors > 0 OR broken_symlinks > 0]
      → [Discord: alert with details]
The health check endpoint verifies: all symlinks resolve to existing files, PocketBase is reachable, NFS mounts are accessible, and no files in the ingest directories are older than 24 hours without being processed.

1. Metadata Confidence Hierarchy
When resolving which metadata value to use for a work's canonical fields, the system picks the highest-confidence source:

Source
Confidence
Notes
Manual edit (PocketBase UI)
100
Your override is always final. Created when you edit a field in the UI.
MusicBrainz (via beets)
95
Community-verified, standardized. The gold standard.
Discogs (via beets)
85
Excellent for South Asian physical releases. Less standardized.
Tidal/Qobuz file tags
80
Commercial tags are usually correct. May have transliteration inconsistencies.
LLM normalization
70
Good for transliteration and genre. Unreliable for factual claims (year, album). Validated by Pydantic.
YouTube / .info.json (Yubal)
60
User-uploaded metadata. Good for title/artist, weak for album/genre.
Adhoc file tags
40
Unknown provenance. Could be excellent or garbage.

1. Python Compute Service API Reference
The Python service runs as a FastAPI application in the Proxmox LXC. It exposes these endpoints:

Endpoint
Method
Returns
/api/discover
POST
{ new_files: N, updated_files: N, skipped: N, errors: [] }
/api/analyze
POST
{ analyzed: N, new_works: N, merged_to_existing: N, works_changed: N, needs_review: N }
/api/tag
POST
{ tagged: N, mb_matched: N, llm_cleaned: N, as_is: N }
/api/symlink
POST
{ created: N, updated: N, removed: N, plex_scan_triggered: bool }
/api/mb/batch-submit
POST
{ isrcs_submitted: N, fingerprints_submitted: N, tags_submitted: N }
/api/mb/sync
POST
{ synced: N, new_mbids: N }
/api/health
GET
{ status: ok/error, files_total: N, works_total: N, broken_symlinks: N, last_discover: ts, errors: [] }
/api/work/{id}/reanalyze
POST
Re-runs quality scoring and best-file selection for a specific work. For manual triggers from PocketBase.
/api/work/{id}/seed-url
GET
Returns the MusicBrainz release editor seed URL for this work. Open in browser to submit.

Every endpoint reads from and writes to PocketBase via its REST API (using the pocketbase Python SDK or plain HTTP requests). The Python service does not maintain its own database — PocketBase is the single source of truth.

1. What You See in PocketBase
PocketBase's admin UI is not a custom dashboard — it's a generic database admin interface. But for this use case, it's surprisingly effective. Here's what your daily interaction looks like:
9.1 Browsing Your Catalog
Open the works collection. You see a sortable, searchable table with columns for canonical_title, canonical_artist, genre, mb_status, file_count, and needs_review. PocketBase supports full-text search, column sorting, and custom filters. Filter by needs_review = true to see duplicates needing confirmation. Filter by mb_status = pending to see tracks ready for MusicBrainz submission.
9.2 Inspecting a Work
Click a work record. You see all its fields, including the best_file relation (clickable to jump to the file record). From the files collection, filter by work = [this work's ID] to see all versions with their quality_score, quality_verdict, spectral_ceiling, and source_dir. The highest-scoring file has is_primary = true.
9.3 Editing Metadata
Click any field and type a new value. Hit save. If you've set up the PocketBase realtime hook in n8n (Section 6.3), this triggers the Python service to re-tag the file and update the symlink. Your Plex library reflects the change within seconds.
9.4 Reviewing Quality Alerts
From the files collection, filter by quality_verdict = fake or quality_verdict = suspicious. You see every file the system flagged as a potential upscale, with its spectral_ceiling (the smoking gun) and quality_score. You can manually override is_primary if you disagree with the system's ranking.
9.5 Limitations of PocketBase's UI
To be transparent about what PocketBase doesn't give you:
No inline audio preview. You can't A/B compare versions by clicking play in the UI. You'd need to open the files in a separate player. A future enhancement could be a lightweight custom page that uses PocketBase's API + HTML5 audio.
No visual spectrogram display. The quality data is numeric only. You can generate spectrogram images with SoX and attach them as PocketBase file fields for visual inspection if needed.
No one-click MusicBrainz seeding from the UI. PocketBase can't open external URLs on button click. The workaround: the Python service's /api/work/{id}/seed-url endpoint returns the URL, and n8n can send it to you via Discord when you're ready for a MB submission session.

2. Implementation Roadmap
Phases are ordered by value delivery, with a working system at each checkpoint:
Phase 1: PocketBase + Discovery (Days 1–6)
Day 1–2: Deploy PocketBase as a Docker container on Unraid (or in the Proxmox LXC). Create the three collections: works, files, metadata_sources. Configure fields per Section 3. Set up an admin account.
Day 3–4: Provision the Proxmox LXC for the Python service. Install Python 3.12, ffmpeg, chromaprint-tools. Set up NFS mounts to all ingest directories. Install dependencies: fastapi, uvicorn, mutagen, requests (for PocketBase API calls).
Day 5–6: Write the /api/discover endpoint. Walk all three ingest dirs, extract metadata via mutagen, insert into PocketBase. Wire up n8n to call it on a 15-minute cron. Verify files appear in PocketBase's UI.
Checkpoint: Every audio file across all three directories is visible in PocketBase with raw metadata.
Phase 2: Fingerprinting + Quality + Dedup (Days 7–14)
Day 7–9: Install pyacoustid + fpcalc. Implement fingerprint generation. Implement the two-pass dedup algorithm (fingerprint correlation, then fuzzy metadata). Test against known duplicates across your Yubal and Tidal directories.
Day 10–12: Install FLAC Detective and librosa. Implement the composite quality scoring algorithm. Run it against your entire collection. Calibrate thresholds — spot-check against Fakin’ the Funk results on the same files.
Day 13–14: Wire up /api/analyze. Integrate into the n8n pipeline after discovery. Test the full chain.
Checkpoint: You can see duplicate groups and quality scores in PocketBase. Fake FLACs are flagged.
Phase 3: Symlinks + Plex (Days 15–19)
Day 15–16: Implement the symlink manager. For each work, create a symlink in /media/Music/ pointing to the primary file. Handle the re-pointing logic for when a better version appears.
Day 17–18: Configure Plex to scan /media/Music/. Ensure both the symlink directory and target directories are mounted in Plex's Docker container. Test playback through symlinks.
Day 19: Wire up /api/symlink with Plex scan trigger. Test: drop a new FLAC in tidal-dl/ and verify it appears in Plex within 15 minutes.
Checkpoint: Plex serves the best version of every song. Drop files in any ingest dir and they auto-appear.
Phase 4: Metadata Intelligence (Days 20–26)
Day 20–22: Configure beets with the full config (quiet_fallback: asis, Discogs parity, preferred countries). Run beet import against your library. Process results into metadata_sources.
Day 23–24: Set up Ollama + FastAPI on Windows. Implement the LLM normalization pass. Integrate metadata merging logic (pick highest-confidence value per field).
Day 25–26: Wire up /api/tag. Integrate into the n8n pipeline. Test: verify that works get clean canonical metadata and primary files get correct embedded tags.
Checkpoint: Your Plex library has clean, normalized metadata for every track. Transliteration is standardized.
Phase 5: MusicBrainz Contribution (Days 27–32)
Day 27–29: Install musicbrainzngs and pyacoustid. Build the batch submission endpoint (ISRCs, fingerprints, genre tags). Run a first batch for your matched library.
Day 30–31: Build the seed URL generation endpoint. Set up yambs for CSV-to-seed conversion. Test generating and opening seed URLs for unmatched Pakistani releases.
Day 32: Set up the weekly n8n workflows for MB batch submission and mbsync. End-to-end test: submit a release, wait 24h, verify MBID syncs back.
Checkpoint: The full system is operational. You're actively contributing Pakistani music metadata to MusicBrainz.
Phase 6: Polish + Realtime Hooks (Days 33–35)
Day 33: Set up PocketBase realtime hooks in n8n for the manual edit → re-tag → re-symlink flow.
Day 34: Build the health check endpoint. Wire up n8n to alert on broken symlinks, stale files, or service errors.
Day 35: Documentation. Write a README covering: how to add music (just drop files), how to review duplicates, how to submit to MB, how to override quality decisions.

3. Full Technology Stack

Layer
Tool
Why
YouTube Music sync
Yubal
Already working. Writes to yubal/ directory.
Orchestration
n8n
Already deployed. Visual workflows, cron, retries, Discord.
Database + UI
PocketBase
Single binary. SQLite. Admin UI for free. REST API for n8n + Python.
Compute service
Python + FastAPI
Audio analysis, beets, mutagen, symlinks. Testable functions, not n8n Code nodes.
Audio fingerprinting
pyacoustid + fpcalc
Deduplication across sources. AcoustID contribution.
Quality analysis
FLAC Detective + librosa
Deterministic upscale detection. No GPU needed.
Metadata tagging
beets + mutagen
beets for MB/Discogs matching. mutagen for tag R/W.
Fuzzy matching
thefuzz
Metadata-based dedup fallback.
LLM metadata
Ollama + Llama 3.1 8B
On Windows RTX 3080 Ti. HTTP endpoint.
MusicBrainz
musicbrainzngs + yambs
API submissions + seed URL generation.
Media server
Plex + Plexamp
Follows symlinks. Sonic analysis. Plexamp for listening.
Notifications
Discord (via n8n)
Pipeline summaries, quality alerts, MB submission links.

1. Risk Register

Risk
Severity
Likelihood
Mitigation
PocketBase single-writer SQLite lock under concurrent n8n + Python writes
Med
Low–Med
Pipeline stages run sequentially (n8n chains them). Concurrent writes are rare. PocketBase handles WAL mode. If you hit contention, add a short retry loop in the Python SDK calls.
Broken symlinks after source file deletion/move
Med
Moderate
Health check endpoint verifies all symlinks every 5 min. n8n alerts on broken links. Never manually reorganize files in ingest dirs — treat them as immutable.
Plex can't follow symlinks inside Docker
High
Certain (must configure)
Mount both /media/Music AND /downloads/unseeded/music into Plex's container at the same absolute paths the symlinks use. Validate on Day 17 before proceeding.
LLM hallucination corrupts metadata
Med
High
Pydantic validation on every LLM response. Confidence capped at 70 (below MB, Discogs, and commercial tags). Never auto-submit LLM output to MusicBrainz. Manual edit always overrides.
AcoustID fingerprint collision (two different songs match)
Med
Low
Require correlation > 0.85 AND duration within 10 seconds. False positives go to needs_review queue. Human confirms in PocketBase.
Streaming service blocks tidal-dl / streamrip
High
Low–Moderate
Pipeline is download-agnostic — it processes whatever is in the ingest dirs. If Tidal blocks you, Yubal + adhoc still work. The architecture doesn't depend on any single source.
Initial bulk import overloads analysis stage
Low
Certain (first run)
Run /api/analyze with a batch_size parameter (default 50). Process in chunks over multiple n8n cycles rather than all at once.

1. Open Decisions
PocketBase deployment: Unraid Docker vs. Proxmox LXC? If PocketBase runs in the same LXC as the Python service, inter-process communication is localhost (fastest). If it runs as a Docker container on Unraid, it's closer to the storage but adds a network hop. Recommendation: same LXC as the Python service, since PocketBase is a single binary with negligible resource usage.

SQLite journal mode: PocketBase defaults to WAL (Write-Ahead Logging), which handles concurrent readers well. If you ever hit write contention between n8n and the Python service, consider switching to exclusive mode during heavy batch operations.

Custom PocketBase frontend: PocketBase's admin UI covers 90% of needs. If you later want a dedicated catalog browser with audio preview, spectrogram images, and one-click MB seeding, you can build a lightweight HTML/JS page that uses PocketBase's JavaScript SDK. This is a Phase 2 enhancement, not a launch requirement.

Spectrogram image storage: The Python service can generate spectrogram PNGs with SoX or librosa and upload them to PocketBase as file fields on the files collection. This makes quality investigation visual in the admin UI. Nice to have, not essential.

How to handle cover art: beets' fetchart plugin handles this for matched tracks. For unmatched tracks, Yubal's .info.json includes YouTube thumbnail URLs. The Python service could download these and embed via mutagen. Plex will also fetch art from its own sources.
