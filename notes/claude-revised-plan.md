---
# Prompt

Can you do a deep evaluation of these workflow proposals from previous AI brainstorming? I want you to generate a very detailed concrete plan with your recommendations for implementing this music curation workflow

---
# Response

Music Curation Pipeline
Implementation Plan & Technical Architecture

A Concrete Roadmap for Automated YouTube Music Sync,
Lossless Audio Acquisition, LLM-Powered Metadata Normalization,
and Programmatic MusicBrainz Contribution
for Pakistani Musical Heritage Preservation

Prepared for Jehangir
February 2026
Critical Evaluation & Revised Architecture

1. Executive Evaluation of the Source Proposals
Both documents — the Gemini-generated "Automated Audiophile Curation" blueprint and the Claude conversation transcript — cover the same pipeline but from very different angles. The Gemini document is architecturally ambitious and narratively compelling, proposing a full distributed microservices topology across your Proxmox, Unraid, Windows, and MacBook nodes. The Claude transcript is more pragmatic, grounded in specific tool versions, API realities, and fallback strategies. Neither document alone is sufficient for implementation. Here is a frank assessment of where each gets it right and where each goes wrong.
1.1 Where the Gemini Blueprint Gets It Right
Distributed node architecture: The idea of dedicating your Windows PC as a GPU compute API and keeping orchestration on Proxmox is sound. GPU passthrough into Proxmox LXCs is genuinely painful and unreliable, and treating Windows as a FastAPI endpoint is the pragmatic call.
The "Golden Loop" concept: Framing MusicBrainz contribution as a core pipeline stage rather than an afterthought is the right philosophy. The seeding URL approach for the release editor is exactly how the MB community expects programmatic contributions.
Multi-tier audio forensics: Layering algorithmic checks (redoflacs/auCDtect) with neural network verification is a reasonable defense-in-depth strategy for catching upscaled lossy files.
Storage zone separation: The ingest/processing/library zone model prevents half-processed files from polluting the final Plex library. This is essential for atomicity.
1.2 Where the Gemini Blueprint Is Overengineered or Wrong
The microservices architecture is overkill. Four separate "nodes" communicating via REST APIs and NFS mounts for what is fundamentally a sequential batch pipeline processing maybe 5–20 songs per day is massive over-engineering. This isn't a high-throughput streaming system. A single Proxmox LXC with Huey can orchestrate everything, calling out to the Windows machine only when GPU inference is actually needed.
penthy is discontinued and fat_llama is niche. The Gemini doc recommends both for neural audio analysis, but penthy's GitHub explicitly says "discontinued" and fat_llama is an audio upscaler, not a quality detector. The Claude transcript correctly identifies FLAC Detective and librosa spectral_rolloff as more practical, deterministic alternatives.
The MacBook as a "verification client" is unnecessary complexity. Running Playwright in headed mode on the MacBook for MusicBrainz submissions adds a whole node to the architecture for what is literally clicking a link in a browser. The seeding URL approach works fine — just open the URL on whatever machine you're on.
The LLM system prompt is too simplistic. The example prompt asks for JSON output but doesn't enforce a schema, doesn't handle edge cases like Coke Studio compilations (which have complex multi-artist credits), and doesn't address the common case where the "album" field is unknown for YouTube singles.
n8n is recommended but then never actually used. The implementation roadmap defaults to plain Python scripts. If you're writing Python anyway, Huey with Redis gives you retry logic, periodic scheduling, and task queuing without the 300MB overhead of n8n.
1.3 Where the Claude Transcript Adds Critical Missing Detail
ytmusicapi authentication has changed. The Gemini doc references header-based auth, but ytmusicapi now requires OAuth 2.0 with a YouTube Data API Client ID/Secret and a TV/Limited Input device flow. This is a breaking difference if you follow the Gemini instructions.
quiet_fallback: asis is the essential beets setting. Without this, beets will skip every track it can't match in MusicBrainz, which for Pakistani music could be 60–80% of your library. The Gemini doc doesn't mention this at all.
Discogs as a co-equal metadata source. Setting data_source_mismatch_penalty: 0.0 for Discogs is critical because Discogs has significantly better coverage of South Asian physical releases than MusicBrainz.
The four-tier MusicBrainz contribution model is more nuanced and realistic than the Gemini doc's two strategies. Separating fully automated API submissions (ISRCs, fingerprints, tags) from seeded browser submissions from LLM-assisted data generation gives you a clear decision tree.
yambs (codeberg.org/derat/yambs) for CSV-to-seed-URL generation is a huge time saver the Gemini doc misses entirely.
yubal and SoulSync are existing projects that overlap with parts of this pipeline and should be evaluated before building everything from scratch.

2. Revised Architecture: What to Actually Build
Based on the evaluation above, here is the architecture I recommend. The guiding principle is: minimize moving parts, maximize the use of existing tools, and only write custom code where no tool covers your specific need.
2.1 Infrastructure Topology (Simplified)
The Gemini doc's four-node architecture collapses to two active nodes with Unraid as passive storage:

Node
Role
What Runs Here
Proxmox LXC
Orchestrator + Pipeline
Huey + Redis, ytmusicapi poller, streamrip, yt-dlp, beets, FLAC Detective, librosa, seeding generator, notification webhooks. This is the brain.
Windows PC
GPU API (on-demand)
Ollama + Llama 3.1 8B via FastAPI. Called over HTTP only when LLM metadata cleaning is needed. Machine stays a normal workstation otherwise.
Unraid NAS
Storage + Plex
NFS exports for /ingest, /processing, /library. Runs Plex Media Server in Docker. Passive — no pipeline logic runs here.

The MacBook is deliberately excluded from the architecture. You'll use it to click MusicBrainz seeding URLs in your browser like a normal human, but it's not a pipeline node. No Playwright, no automation scripts, no complexity.
2.2 Pipeline Flow (Six Stages)
Every stage has a primary tool, a fallback, and a clear pass/fail decision:

#

Stage
Primary Tool
Fallback
Runs On
Output
1
Poll
ytmusicapi
—
Proxmox
New videoIds in SQLite queue
2
Download
streamrip (Qobuz → Tidal → Deezer)
yt-dlp (lossy, format 141)
Proxmox
Audio file + .info.json sidecar in /ingest
3
Verify
FLAC Detective + librosa rolloff
SoX spectrogram for manual review
Proxmox
Verified file in /processing or rejected to /review
4
Tag + Clean
beets (MB + Discogs) → mutagen gap-fill
Ollama LLM on Windows (HTTP)
Proxmox + Windows
Fully tagged file with mb_status flag
5
Organize
beets paths + plexupdate
—
Proxmox → Unraid
File in Plex-compatible path on NAS
6
Contribute
musicbrainzngs + yambs + seeding URLs
Manual MB editor
Proxmox + Browser
MBIDs written back to file tags

1. Stage-by-Stage Implementation Details
3.1 Stage 1: YouTube Music Polling
Authentication Setup
Critical correction: The Gemini doc's instruction to copy browser request headers is outdated. ytmusicapi now uses OAuth 2.0. You need a Google Cloud project with the YouTube Data API v3 enabled and an OAuth Client ID of type "TV and Limited Input devices." The setup command is ytmusicapi oauth, which walks you through the device code flow and generates an oauth.json file with refresh tokens. This file is your credential — mount it as a secret in the Proxmox LXC.
Polling Logic
The core poller is straightforward, but the Gemini doc misses several practical concerns:
Polling interval: Every 30 minutes is fine (not 6 hours as Gemini suggests). ytmusicapi doesn't hit official API quotas because it reverse-engineers internal endpoints. But add jitter (random 0–60 second delay) to avoid looking like a clockwork bot to Google.
State tracking: SQLite table with columns: video_id (PK), title, artist_name, album_name, thumbnail_url, duration_seconds, discovered_at, status (queued/downloading/downloaded/failed/skipped), local_path, mb_status (unknown/matched/pending/submitted).
Deduplication before download: The Gemini doc's three-layer verification (beets DB → PlexAPI → fuzzy matching) is sound in theory but overbuilt for the initial implementation. Start with just: (a) check if video_id exists in SQLite, (b) run thefuzz token_sort_ratio against your beets DB with thresholds of 85 for title and 90 for artist. Add PlexAPI queries later if you're getting false negatives.
Recommended Code Structure

```python
# ytm_poller.py

from ytmusicapi import YTMusic
import sqlite3, time, random

yt = YTMusic('oauth.json')
db = sqlite3.connect('pipeline.db')

def poll_liked_songs():
    time.sleep(random.randint(0, 60))  # jitter
    liked = yt.get_liked_songs(limit=None)
    existing_ids = set(r[0] for r in db.execute(
        'SELECT video_id FROM tracks').fetchall())
    new_tracks = [t for t in liked['tracks']
                  if t['videoId'] not in existing_ids]
    for track in new_tracks:
        db.execute('INSERT INTO tracks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (track['videoId'], track['title'],
             track['artists'][0]['name'] if track['artists'] else 'Unknown',
             track.get('album', {}).get('name', ''),
             track.get['thumbnails', [{}]](-1).get('url', ''),
             track.get('duration_seconds', 0),
             int(time.time()), 'queued', None))
    db.commit()
    return new_tracks
```

Important note on yt.get_liked_songs(): The limit=None parameter fetches all liked songs. On the first run this could be hundreds or thousands of tracks. Build an initial import mode that processes these in batches of 20 with delays between batches to avoid hammering streamrip.
3.2 Stage 2: Lossless Audio Acquisition
Source Priority and Search Strategy
The Gemini doc's source prioritization is correct, but the implementation is harder than either document acknowledges:

Priority
Source
Max Quality
Requirement
Pakistani Music Coverage
1
Qobuz
24-bit/192kHz FLAC
Sublime+ subscription
Poor. Mostly Coke Studio and major label reissues.
2
Tidal
16-bit/44.1kHz FLAC
HiFi Plus subscription
Moderate. Better for mainstream Pakistani pop.
3
Deezer
16-bit/44.1kHz FLAC
HiFi subscription
Best of the three for South Asian catalogs.
4
YouTube Music
256kbps AAC (format 141)
Premium subscription
Excellent. Often the only source for indie/underground.

The Cross-Provider Search Problem
This is the hardest unsolved piece of the pipeline. No existing tool searches across Qobuz, Tidal, and Deezer to find the best available quality for a given track. streamrip can search each individually, but the matching logic — especially for transliterated Urdu titles — needs to be custom-built.
My recommended approach:
Search by ISRC first. If the YouTube Music metadata includes an ISRC (check the .info.json sidecar), use it as the primary search key. ISRCs are universal identifiers that work across all providers.
Fall back to normalized artist + title. Strip diacritics, lowercase, remove common suffixes ("(Official Video)", "| Coke Studio"), then search each provider with streamrip's CLI.
Duration-based verification. The Gemini doc correctly notes that a duration delta >5 seconds likely indicates a different version. Implement this.
Cache search results. Store provider search results in SQLite so you don't re-search for the same track across retries.
yt-dlp as Last Resort
When no lossless source exists (common for indie Pakistani hip-hop, underground Urdu rap, YouTube-first releases), use yt-dlp with format 141 (256kbps AAC). Never convert lossy audio to FLAC — keep it as .m4a:
yt-dlp -f 141 \
  --embed-metadata --embed-thumbnail --write-info-json \
  --cookies-from-browser chrome \
  -o '/mnt/ingest/%(artist)s/%(title)s.%(ext)s' \
  '<https://music.youtube.com/watch?v={video_id}>'

The --write-info-json flag is essential. The .info.json sidecar preserves every field YouTube Music provides (including album, track number, upload date, and description) for later enrichment by mutagen and the LLM.
3.3 Stage 3: Audio Quality Verification
My recommendation diverges from both source documents here. Skip the neural network approach entirely for now. It adds complexity (GPU dependency, model maintenance, inference latency) for marginal gain over deterministic tools.
Tier 1: FLAC Detective (Deterministic, pip-installable)
FLAC Detective uses an 11-rule scoring system that classifies files into four categories: AUTHENTIC, WARNING, SUSPICIOUS, or FAKE_CERTAIN. Install it with pip install flac-detective and integrate it as a Python function call:
from flac_detective import analyze

result = analyze('track.flac')
if result.verdict in ('AUTHENTIC', 'WARNING'):
    move_to_processing(track)
elif result.verdict == 'SUSPICIOUS':
    flag_for_review(track, result.report)
else:  # FAKE_CERTAIN
    move_to_rejected(track, result.report)
Tier 2: librosa Spectral Rolloff (Supplementary)
For files FLAC Detective flags as WARNING or SUSPICIOUS, compute the spectral rolloff to estimate the effective frequency ceiling:
import librosa
import numpy as np

y, sr = librosa.load('track.flac', sr=None)
rolloff = librosa.feature.spectral_rolloff(
    y=y, sr=sr, roll_percent=0.99)
effective_ceiling = np.mean(rolloff)

# Genuine 16-bit/44.1kHz: ~20-22 kHz

# Upscaled 128kbps MP3:   ~16 kHz

# Upscaled 320kbps MP3:   ~19-20 kHz

if effective_ceiling < 17000:
    verdict = 'LIKELY_UPSCALE'
elif effective_ceiling < 19500:
    verdict = 'POSSIBLE_UPSCALE'
else:
    verdict = 'LIKELY_AUTHENTIC'
Handling Rejected Files
Both documents agree on this: don't delete rejected files. Move them to /review/upscales/ on Unraid. Generate a spectrogram image with SoX and send a Discord/Telegram notification with the verdict and spectrogram. For rare Pakistani recordings where the upscale is the only existing copy, you'll want to keep it with a quality_note tag.
3.4 Stage 4: Metadata Tagging & LLM Enrichment
This is the stage where the pipeline's Pakistani music specialization actually matters. The strategy is three-pass:
Pass 1: beets Auto-Import
Run beet import -q on verified files. The critical beets config:

```yaml
# ~/.config/beets/config.yaml

directory: /mnt/library/music
library: /mnt/library/beets.db

import:
  write: yes
  copy: yes
  quiet: yes
  quiet_fallback: asis    # THIS IS THE KEY SETTING
  log: /var/log/beets/import.log
  languages: [en, ur, hi, pa]

match:
  strong_rec_thresh: 0.04
  preferred:
    countries: [PK, IN, US, GB]

musicbrainz:
  data_source_mismatch_penalty: 0.0

discogs:
  data_source_mismatch_penalty: 0.0

plugins: discogs chroma fetchart embedart scrub
  replaygain plexupdate fromfilename mbsync

paths:
  default: $albumartist/$album%aunique{}/$disc$track $title
  singleton: Non-Album/$artist/$title
  comp: Various Artists/$album%aunique{}/$disc$track $title

plexupdate:
  host: <unraid-ip>
  port: 32400
  token: <plex-token>
  library_name: Music
```

After this pass, files fall into two buckets: (a) matched by MusicBrainz or Discogs with high confidence and tagged with MBIDs, or (b) imported as-is with whatever tags they had from YouTube/streamrip. Files in bucket (b) get mb_status: unmatched in your SQLite tracking DB.
Pass 2: mutagen Gap-Fill from .info.json
For files that beets imported as-is, read the .info.json sidecar saved by yt-dlp and fill any missing tags:

```python
from mutagen import File
import json, os

def fill_gaps(audio_path, info_json_path):
    info = json.load(open(info_json_path))
    audio = File(audio_path, easy=True)

    field_map = {
        'title': info.get('track') or info.get('title'),
        'artist': info.get('artist') or info.get('uploader'),
        'album': info.get('album', ''),
        'date': info.get('release_date', info.get('upload_date', ''))[:4],
    }

    for tag, value in field_map.items():
        if value and not audio.get(tag):
            audio[tag] = [str(value)]
    audio.save()
```

Pass 3: LLM Metadata Normalization (On-Demand)
This is where the Windows GPU earns its keep. A FastAPI server on the Windows PC exposes Ollama with Llama 3.1 8B (Q4_K_M quantization, ~5–6GB VRAM). The Proxmox orchestrator sends raw metadata, gets back cleaned and structured JSON.
My recommended system prompt is significantly more detailed than either source document's version. The prompt must handle Coke Studio's complex multi-artist credits, the singleton release culture, genre inference from contextual clues, and correct Urdu transliteration:
SYSTEM_PROMPT = '''
You are a Pakistani music metadata specialist. Your task is to
clean and normalize metadata for archival quality. Rules:

TRANSLITERATION:

- Use the most common English spelling for Pakistani artists
- 'Khan' not 'Khaan', 'Fateh' not 'Fatteh'
- Preserve honorifics: 'Ustad' for classical masters
- Split compound credits: 'Rahat Fateh Ali Khan & Party'
  -> artist: 'Rahat Fateh Ali Khan', group: 'Party'

COKE STUDIO HANDLING:

- If title contains 'Coke Studio', extract season/episode
- Album format: 'Coke Studio Season {N}'
- Multiple artists get proper credit splitting
- e.g. 'Kana Yaari, CS14' ->
  title: 'Kana Yaari',
  album: 'Coke Studio Season 14',
  artists: [identified from knowledge]

GENRE INFERENCE:

- Qawwali, Ghazal, Sufi Rock, Pakistani Pop, Urdu Rap
- Never use generic 'World' or 'International'
- Infer from artist/title context if not explicit

OUTPUT: Return ONLY valid JSON with keys:
  artist, album_artist, title, album, year, genre,
  featured_artists (list), language (ISO 639-3),
  script (ISO 15924), country (ISO 3166-1),
  is_compilation (bool), confidence (0-100)
'''

Validation is non-negotiable. Wrap every LLM response in a Pydantic model. If the JSON is malformed or missing required fields, retry with a higher temperature (0.3 → 0.7) up to 3 times, then fall back to the raw tags. Never let hallucinated metadata into the library.
3.5 Stage 5: Library Organization
This stage is almost entirely handled by beets' path configuration. The key decisions:
Singletons go to Non-Album/{artist}/{title}. This is the correct Plex-compatible structure for tracks without album context — common for YouTube-first Pakistani releases.
Compilations (Coke Studio, Nescafé Basement) use Various Artists/{album}. This prevents Plex from creating dozens of phantom artist entries.
cover.jpg per album folder. The fetchart and embedart beets plugins handle this automatically. For singletons, embed the YouTube thumbnail as cover art.
Trigger Plex scan after every import batch. The plexupdate plugin does this. Enable both "Sonic analysis" and "Analyze audio tracks for loudness" in Plex server settings to unlock Plexamp's best features.
3.6 Stage 6: MusicBrainz Contribution (The Golden Loop)
This is the most important stage from a community impact perspective. The four-tier model from the Claude transcript is the right framework, but needs concrete implementation details:
Tier 1: Fully Automated (No Human Needed)
For tracks that already have MBIDs from beets matching:
Submit ISRCs: Scan your library with mutagen, extract any ISRC tags from Qobuz/Tidal downloads, and submit via musicbrainzngs.submit_isrcs(). This is the single highest-value, lowest-effort contribution.
Submit AcoustID fingerprints: Use pyacoustid to generate and submit fingerprints linked to recording MBIDs. Every fingerprint makes the next person's matching easier.
Submit genre tags: Use musicbrainzngs.submit_tags() for genre tags (Qawwali, Ghazal, Sufi Rock, etc.) that are systematically missing for Pakistani recordings.
All three of these run as a batch job — schedule them weekly via Huey. Zero human intervention needed.
Tier 2: AcoustID for Unmatched Files
Even files without MBIDs can have fingerprints submitted with title/artist/duration metadata. This is less precise but still contributes to the fingerprint database. Run this on your entire library as a one-time batch, then incrementally for new imports.
Tier 3: Seeded Submissions (One Click Per Release)
For new releases that don't exist in MusicBrainz at all:
Use yambs (codeberg.org/derat/yambs) to generate seed URLs from your tagged FLAC metadata. yambs reads TSV/CSV files and constructs the correct POST body for the MusicBrainz release editor. This saves you from building your own seeding generator.
Build a simple "pending submissions" page. A Flask page listing unsubmitted releases with a "Seed in MusicBrainz" button per row. Clicking the button constructs the seed URL and opens it in your browser with all fields pre-filled.
Rate limit yourself: 1 release every 5–10 minutes. Add edit notes like "Data from verified FLAC download, tags confirmed against [source]. Contributing Pakistani music metadata." The MB community respects this.
Tier 4: LLM-Assisted Data Generation
For complex submissions where you need structured MB-specific fields (ISO language codes, script codes, artist sort names), use the Ollama endpoint to generate the seed parameters. The LLM is particularly good at:
Artist sort names for Pakistani naming conventions: "Khan, Nusrat Fateh Ali" (MusicBrainz expects Last, First format)
Language/script disambiguation: Urdu (urd/Arab) vs. Punjabi (pan/Guru vs. pan/Arab) vs. Hindi (hin/Deva)
Release type inference: Single vs. EP vs. Album vs. Soundtrack (critical for MB's release group types)
Edit note generation from file metadata context
The mbsync Feedback Loop
After you submit a release and it goes live on MusicBrainz (typically instant for new additive edits), schedule beet mbsync to run 24 hours later. beets will find the release you just added (matching by track lengths and titles), update local tags with official MBIDs, and Plexamp will unlock "Sonically Similar" and other features. This closes the loop: your local library contributed data to the global database, and the global database enriches your local library.

1. Orchestration Architecture
4.1 Why Huey + Redis (Not n8n, Not Airflow)
The decision matrix is simple:

Option
RAM
Scheduling
Retry Logic
Monitoring
Verdict
Huey + Redis
~50 MB
Built-in crontab
Built-in retries
Redis monitor + logs
RECOMMENDED
n8n
~300 MB
Web UI cron
Built-in
Web dashboard
Overkill for this
Plain cron
~0 MB
System cron
Manual
Log files only
Too bare-bones
Airflow
~4 GB
DAG scheduler
Built-in
Full web UI
Absurdly heavy

Huey gives you everything you need in ~50 lines of Python. The full orchestrator:

# orchestrator.py

from huey import RedisHuey, crontab

huey = RedisHuey('music-pipeline',
                  host='localhost', port=6379)

@huey.periodic_task(crontab(minute='*/30'))
def poll_youtube_music():
    new_tracks = poll_liked_songs()  # Stage 1
    for track in new_tracks:
        process_track.schedule(args=(track,), delay=60)

@huey.task(retries=3, retry_delay=300)
def process_track(track):
    path = download_track(track)      # Stage 2
    if path.endswith('.flac'):
        if not verify_quality(path):   # Stage 3
            move_to_review(path, track)
            notify_discord(f'Quality check failed: {track}')
            return
    tag_and_clean(path, track)         # Stage 4
    organize(path)                     # Stage 5
    queue_mb_contribution(track)       # Stage 6 prep

@huey.periodic_task(crontab(day_of_week='0', hour='3'))
def weekly_mb_batch():
    submit_isrcs()      # Tier 1
    submit_fingerprints() # Tier 1
    submit_genre_tags()   # Tier 1

@huey.periodic_task(crontab(day_of_week='1', hour='4'))
def weekly_mbsync():
    subprocess.run(['beet', 'mbsync'])
4.2 Notification Strategy
Use a single Discord webhook for all pipeline notifications. Each notification type gets a different embed color:
Green: Track successfully processed and added to library
Yellow: Track imported as-is (no MusicBrainz match), queued for LLM cleaning
Red: Quality check failed, moved to review
Blue: New MusicBrainz seeding URL ready for review

1. Proxmox LXC Container Setup
A single unprivileged Ubuntu 24.04 LXC container handles everything except GPU inference:
5.1 Container Specs
CPU: 2 cores
RAM: 2 GB (1 GB for pipeline, 512 MB for Redis, 512 MB buffer)
Disk: 20 GB (OS + Python packages + SQLite DBs + beets DB)
Network: Bridge to LAN (needs access to Unraid NFS and Windows PC)
5.2 NFS Mount Configuration

```text
# /etc/fstab in the LXC

<unraid-ip>:/mnt/user/data/ingest    /mnt/ingest    nfs4 rw,soft,timeo=30 0 0
<unraid-ip>:/mnt/user/data/processing /mnt/processing nfs4 rw,soft,timeo=30 0 0
<unraid-ip>:/mnt/user/data/review     /mnt/review    nfs4 rw,soft,timeo=30 0 0
<unraid-ip>:/mnt/user/media/music     /mnt/library   nfs4 rw,soft,timeo=30 0 0
```

5.3 Software Installation

# System packages

apt update && apt install -y python3.12 python3-pip python3-venv \
  ffmpeg sox redis-server git chromaprint-tools

# Python environment

python3 -m venv /opt/music-pipeline
source /opt/music-pipeline/bin/activate

pip install ytmusicapi streamrip yt-dlp beets[discogs,chroma,web] \
  mutagen musicbrainzngs pyacoustid huey[redis] thefuzz \
  flac-detective librosa pydantic requests

# Verify beets plugins

beet version  # should list all enabled plugins
5.4 Windows FastAPI Server Setup
On the Windows PC, the FastAPI server is lightweight:

# Install on Windows (PowerShell)

pip install fastapi uvicorn ollama pydantic

# Pull the model

ollama pull llama3.1:8b-instruct-q4_K_M

# Run the server (add to startup if desired)

uvicorn llm_server:app --host 0.0.0.0 --port 5000

Use FastAPI over Flask (despite the Gemini doc's example using Flask). FastAPI gives you automatic OpenAPI docs at /docs, Pydantic request/response validation built-in, and async support for non-blocking inference.

1. Implementation Roadmap
The Gemini doc's 30-day timeline is reasonable but the phase boundaries are wrong. Here's a revised roadmap that accounts for the dependency chain and lets you get value at each checkpoint:
Week 1: Foundation + First Download (Days 1–7)
Day 1–2: Provision Proxmox LXC. Install all system packages. Configure NFS mounts to Unraid. Verify you can read/write to all four zones from the container.
Day 3: Set up ytmusicapi OAuth. Run the first get_liked_songs() call manually. Create the SQLite schema. Verify you get your full liked playlist.
Day 4–5: Configure streamrip with your streaming service credentials (config.toml). Test manual downloads: search for a well-known Pakistani track on each provider, verify you get FLAC files.
Day 6–7: Install and test yt-dlp fallback. Write the basic download_track() function that tries streamrip first, falls back to yt-dlp. Verify .info.json sidecars are written.
Checkpoint: You can manually trigger a download of any track from your liked playlist in the best available quality.
Week 2: Quality Gate + Basic Tagging (Days 8–14)
Day 8–9: Install and test FLAC Detective and librosa. Run them against your test downloads. Calibrate thresholds by testing against known-good and known-bad files.
Day 10–11: Configure beets with the full config.yaml. Run beet import manually on your test files. Verify quiet_fallback: asis works correctly for unmatched tracks.
Day 12–13: Write the mutagen gap-fill script. Test it against files imported as-is. Verify that .info.json data correctly fills missing tags.
Day 14: Set up Redis. Install Huey. Wire up the polling task and the process_track pipeline. Run the first fully automated cycle: poll → download → verify → tag → organize.
Checkpoint: New liked songs automatically appear in your Plex library within ~30 minutes.
Week 3: LLM Intelligence + Notifications (Days 15–21)
Day 15–16: Set up Ollama + FastAPI on Windows. Pull Llama 3.1 8B. Test the /clean_metadata endpoint from the Proxmox container with curl.
Day 17–19: Develop and iterate on the system prompt. Test with your hardest cases: Coke Studio multi-artist tracks, Urdu-only titles, classical Qawwali with honorifics. Refine until the Pydantic validation pass rate exceeds 90%.
Day 20: Integrate LLM cleaning into the pipeline as a post-beets pass. Files that beets imports as-is get sent to the LLM for normalization.
Day 21: Set up Discord webhook notifications. Test all four notification types.
Checkpoint: Pipeline handles even obscure Pakistani music with clean, normalized metadata.
Week 4: MusicBrainz Contribution (Days 22–30)
Day 22–23: Install musicbrainzngs and pyacoustid. Write and test the ISRC submission script. Submit ISRCs for your existing matched library.
Day 24–25: Write the AcoustID fingerprint submission script. Run it against your full library as a one-time batch.
Day 26–27: Install yambs. Create a TSV template from your unmatched files' metadata. Test generating seeding URLs and verify the MusicBrainz release editor opens pre-filled correctly.
Day 28–29: Build the "pending submissions" Flask dashboard. List unsubmitted releases with one-click seeding buttons.
Day 30: End-to-end test: Like a new song on YouTube Music. Watch it download, verify, tag via LLM, organize into Plex, and generate a MusicBrainz seeding URL. Click the link, submit the release, wait 24h, run mbsync, verify the MBID appears in your local tags.
Checkpoint: The full pipeline runs autonomously. You spend ~30 minutes/week reviewing MusicBrainz submissions.

2. Tools and Approaches to Skip
Both source documents mention tools that are dead, deprecated, or not worth the complexity:

Tool/Approach
Status
Use Instead
penthy
Discontinued (per GitHub)
FLAC Detective + librosa spectral rolloff
fat_llama
Audio upscaler, not detector
Not needed — this solves a different problem
Deemix
Dead since 2022
streamrip (supports Deezer natively)
Tidal-Media-Downloader
Auth broken since Oct 2025
streamrip (supports Tidal natively)
Lidarr
100% MusicBrainz dependent
Custom pipeline (this doc)
Playwright on MacBook
Unnecessary complexity
Just click the seeding URL in any browser
n8n
Works but overkill here
Huey + Redis (≥50 MB RAM vs ≥300 MB)
Votify (Spotify)
Account suspension risk
Not worth the risk — use official streaming APIs

1. Existing Projects Worth Evaluating First
Before building everything custom, spend a day evaluating these two projects that overlap significantly with your pipeline:
8.1 yubal (github.com/guillevc/yubal)
Purpose-built for YouTube Music → organized library conversion. It uses ytmusicapi + yt-dlp, applies Spotify metadata enrichment, syncs playlists, and produces a clean Artist/Year-Album/Track structure with Docker deployment. If yubal handles your basic sync needs, you can focus your custom development effort entirely on the LLM metadata layer and MusicBrainz contribution stages — which are the parts where no existing tool covers your use case.
8.2 SoulSync (github.com/Nezreka/SoulSync)
The most ambitious project in this space (~100k lines of code) integrating Spotify, Tidal, YouTube, slskd (Soulseek), MusicBrainz, AcoustID, ListenBrainz, and Plex/Jellyfin/Navidrome. May be too heavy and opinionated, but evaluate whether its download orchestration layer could save you from writing cross-provider search logic.
8.3 Harmony (harmony.pulsewidth.org.uk)
The MusicBrainz community's recommended tool for imports. It aggregates metadata from Deezer, Spotify, Apple Music, and iTunes, harmonizes it, and seeds the MusicBrainz release editor. Use this for batch submissions of releases that exist on DSPs but not in MusicBrainz.

2. Risk Register and Mitigations

Risk
Severity
Likelihood
Mitigation
ytmusicapi OAuth tokens expire or Google changes internal API
High
Moderate (happens every 6–12 months)
Pin ytmusicapi version. Monitor GitHub issues. Token refresh is built-in; full re-auth takes 2 minutes.
Streaming service blocks streamrip
High
Low–Moderate (Deezer most likely)
Multi-provider fallback chain. Keep yt-dlp as last resort. Don't hammer any single provider.
LLM hallucinates incorrect metadata
Medium
High (LLMs hallucinate by nature)
Pydantic validation, confidence threshold (reject <70), human review for MB submissions, never auto-submit LLM output to MB.
MusicBrainz bot policy violation / account ban
High
Low (if you follow rate limits)
Always use seeding (human clicks Submit). Rate limit to 1 release/10 min. Register a bot account if exceeding 100 edits/day.
NFS mount instability causes file corruption
High
Low
Use soft mounts with timeouts. Stage all writes to /processing before moving to /library atomically. Never write directly to the library zone.
Initial import overwhelms pipeline (1000+ liked songs)
Low
Certain (first run)
Batch initial import: process 20 tracks, sleep 10 min, repeat. Use Huey's delay parameter.

1. Final Recommendations
Start with the minimum viable pipeline (Stages 1–5) before touching MusicBrainz contribution. Getting songs from YouTube Music into Plex with decent tags is immediately useful. MusicBrainz contribution is important for the community but not for your daily listening experience. Ship the basic pipeline first.

Evaluate yubal before writing your own poller/downloader. If it handles 80% of the sync workflow, your custom code shrinks to just the LLM cleaning + MB contribution stages.

Don't over-invest in audio quality detection. FLAC Detective + librosa covers 95% of cases. The remaining 5% are edge cases (vintage analog transfers, unusual mastering) where a spectrogram and human ears are better than any algorithm.

The LLM is a metadata assistant, not a decision-maker. Every LLM output must be validated (Pydantic), thresholded (confidence score), and never auto-submitted to MusicBrainz. Use it to generate draft metadata and seed parameters, then review before committing.

Your MusicBrainz contributions will have outsized impact. Pakistani music is severely underrepresented in MB. Every release you add, every ISRC you submit, every fingerprint you contribute makes the database better for the entire global community of Pakistani music listeners. This is genuinely valuable cultural preservation work.

Keep the architecture simple. Two active nodes (Proxmox LXC + Windows GPU API), one storage node (Unraid), one task queue (Huey + Redis). If the temptation arises to add Kubernetes, service meshes, or message brokers — resist. You're processing maybe 50 tracks a week, not running Spotify.

---

# Prompt

Okay thanks. So I want to make a few changes based on:

- I prefer n8n over huey because I already have that deployed fora different automation use case
- I tried out Yubal and it seems to work well enough for the YouTube playlist syncing aspect
- so now I have a couple of folders on my NAS that I need to organize and ingest: "/mnt/user/main/downloads/unseeded/music/tidal-dl", "/mnt/user/main/downloads/unseeded/music/yubal", "/mnt/user/main/downloads/unseeded/music/adhoc"
- what I want to do here is:
  - Yubal handles the continuous syncing and first pass downloading of files from my YouTube playlists
  - then I can bulk download into tidal-dl or have one-off files downloaded in the adhoc directory
  - I want the curation workflow to look through all these, do smart matching to figure out a superset list of all songs I have downloaded and maintain that as a user-friendly web UI backed by a clean database or something, update or clean metadata, then do symlinks into "/mnt/user/main/media/Music" for the best version of each song
  - the best version is the highest quality version. However I have found (through Fakin the Funk) that FLAC files on Tidal are sometimes just reencodes of lossy files, especially from indie artists. So I want this to be smarter than just based on stated bitrate or file extension

I asked another AI model and it recommended PocketBase and relying more on n8n than creating a web app from scratch. What do you think?

---

# Response

Good question — let me give you a frank comparison rather than just defending my earlier recommendation.

**PocketBase is a smart suggestion for your situation.** The other model correctly identified that building a FastAPI + Jinja2 web app from scratch is a lot of work for what is essentially a CRUD interface over a SQLite database. PocketBase gives you a usable admin UI, REST API, and SQLite backend in a single binary with zero code. That's genuinely appealing.

**However, there are real tradeoffs to consider:**

**Where PocketBase works well for you:** It eliminates the entire "Phase 4: Web UI (Days 18–24)" from my roadmap. You get a searchable, filterable table interface for free. The REST API means n8n can read/write the database without custom code. And you already have n8n deployed, so leaning into it as the orchestration layer makes sense — you don't need to build a parallel FastAPI backend when n8n can chain HTTP calls to PocketBase.

**Where the PocketBase approach has real limitations:**

The schema the other model proposed is too simple. Two tables (`Tracks` and `Files`) without a metadata provenance layer means you lose the ability to track *why* a particular title or artist name was chosen. When the LLM normalizes "NFAK" to "Nusrat Fateh Ali Khan," you want to know that happened and be able to revert it. My `metadata_sources` table solves this; PocketBase can absolutely hold this table, but the other model didn't include it.

The other model's plan puts too much logic inside n8n. Fingerprint comparison, fuzzy matching, quality scoring, symlink management — doing all of this in n8n's "Execute Command" and "Code" nodes means your pipeline logic is scattered across n8n workflow nodes rather than in testable, version-controllable Python code. n8n is great as a scheduler and glue layer, but it's a poor place to implement an AcoustID correlation algorithm or a composite quality scoring function. When something breaks, debugging a chain of n8n nodes is significantly harder than debugging a Python function with a stack trace.

The quality scoring in the other model's plan is oversimplified. It assigns fixed point values (FLAC = 100, AAC 256 = 75, etc.) rather than analyzing the actual audio signal per file. This is exactly the approach that fails for your Tidal upscale problem — a fake FLAC would still score 100 until FLAC Detective separately flags it, and the interaction between those two signals isn't handled.

**My recommended hybrid approach:**

Use PocketBase as the database + admin UI (the other model is right about this), but keep a lightweight Python service for the compute-heavy work that doesn't belong in n8n nodes. Here's how the responsibilities divide:

| Layer | Tool | Responsibility |
| --- | --- | --- |
| Scheduling + glue | **n8n** | Cron triggers, chaining stages, conditional branching, Discord notifications, health checks |
| Database + UI | **PocketBase** | Schema, REST API, admin interface for browsing/editing the catalog, real-time event hooks |
| Compute | **Python service** | Fingerprinting, spectral analysis, quality scoring, beets integration, mutagen tag R/W, symlink management, MB seed generation |

The Python service exposes 4–5 HTTP endpoints that n8n calls — essentially the same `/api/discover`, `/api/analyze`, `/api/tag`, `/api/symlink` design from my v2 plan, but instead of the Python service owning the database, it reads from and writes to PocketBase via its REST API. This means:

- You get PocketBase's free admin UI for browsing and manual edits
- Pipeline logic lives in testable Python, not n8n Code nodes
- n8n orchestrates the flow without containing complex algorithms
- PocketBase's realtime subscriptions can trigger n8n workflows when you manually edit a record in the UI (the other model correctly noted this is powerful)

The schema in PocketBase would be three collections: `works` (the abstract song identity), `files` (concrete audio files with quality scores), and `metadata_sources` (provenance tracking). Same data model as my v2 plan, just hosted in PocketBase instead of raw SQLite.

This gives you the best of both suggestions — PocketBase's zero-code UI and the robustness of real Python for audio analysis — without the downside of either (building a web UI from scratch, or cramming spectral analysis into n8n nodes).

---
