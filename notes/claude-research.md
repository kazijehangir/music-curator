# Self-Hosted Music Curation Pipeline: Research Notes

No single tool does everything you need, but a combination of **ytmusicapi**, **yt-dlp**, **streamrip**, **beets**, and a lightweight orchestrator like Huey or n8n can form a robust automated pipeline.

The biggest challenge for Pakistani/South Asian music is MusicBrainz's poor coverage — this affects not just tagging but also Lidarr and every tool built on MusicBrainz. The recommended architecture uses YouTube Music metadata as the primary source of truth, attempts MusicBrainz/Discogs matching opportunistically, and falls back gracefully to as-is imports.

> **Note:** True lossless audio requires paid Qobuz/Tidal/Deezer subscriptions via streamrip; YouTube Music caps at 256 kbps lossy even with Premium.

---

## Table of Contents

1. [YouTube Music Playlist Sync](#1-youtube-music-playlist-sync)
2. [Audio Downloading](#2-audio-downloading)
3. [Metadata Tagging](#3-metadata-tagging)
4. [MusicBrainz Contribution](#4-musicbrainz-contribution)
5. [Local LLM Usage](#5-local-llm-usage)
6. [Plex Library Structure](#6-plex-library-structure)
7. [Orchestration](#7-orchestration)
8. [Existing Projects](#8-existing-projects)
9. [Recommended Architecture](#9-recommended-architecture)
10. [MusicBrainz Submission Strategies](#10-musicbrainz-submission-strategies)

---

## 1. YouTube Music Playlist Sync

**Primary tool:** [ytmusicapi](https://github.com/sigma67/ytmusicapi) (2.3k stars, actively maintained, MIT license)

ytmusicapi reverse-engineers YouTube Music's internal API endpoints, giving access to YTM-specific features that Google's official YouTube Data API v3 doesn't expose. Authentication now requires OAuth 2.0 with a YouTube Data API Client ID/Secret from Google Cloud Console, using a TV/Limited Input device flow that generates a persistent `oauth.json` with refresh tokens.

### Fetching Liked Songs

`yt.get_liked_songs(limit=None)` returns every track in the "Liked Music" playlist (internal ID `LM`), each with:

- `videoId`, `title`, `artists` (list with name/ID), `album` (name/ID)
- `duration`, `thumbnails`, `likeStatus`

The list comes ordered newest-first, so a polling strategy stores `videoId` values in SQLite and computes set differences on each run. There are no webhooks or push notifications — **polling is the only option**.

### Why Not the Official YouTube Data API v3?

| Issue | Detail |
|---|---|
| Wrong playlist | Accesses generic "Liked Videos" (LL), not YTM's "Liked Music" (LM) |
| Quota limits | 10,000 units/day |
| No service accounts | OAuth with user consent only |
| Missing features | No YTM-specific metadata |

For lightweight enumeration without downloading, yt-dlp supports `--flat-playlist --dump-single-json` to extract playlist metadata as JSON (requires `--cookies-from-browser chrome` for private playlists). However, ytmusicapi is more reliable for ongoing sync.

---

## 2. Audio Downloading

### YouTube Audio Quality Ceiling

YouTube Music **never serves lossless audio**. Maximum quality tiers:

| Format | Codec | Bitrate | Requirement |
|---|---|---|---|
| 251 | Opus | ~128–160 kbps | Free |
| 140 | AAC LC | 128 kbps | Free |
| 774 | Opus | 256 kbps | YT Music Premium |
| 141 | AAC LC | 256 kbps | YT Music Premium |

**Prefer format 141** (256 kbps AAC) over 774 (256 kbps Opus) — Opus 774 applies a 20 kHz lowpass filter and resamples to 48 kHz, while AAC 141 preserves the original 44.1 kHz sample rate. **Converting YouTube audio to FLAC creates a larger file with zero quality improvement — avoid this.**

Best yt-dlp invocation for YouTube Music Premium:

```bash
yt-dlp -f 141 --embed-metadata --embed-thumbnail --write-info-json \
  --cookies-from-browser chrome \
  -o "%(artist)s/%(album)s/%(track_number)02d %(title)s.%(ext)s" URL
```

### True Lossless Audio

Requires paid streaming subscriptions. **[Streamrip](https://github.com/nathom/streamrip)** (v2.1.0 March 2025, actively maintained) is the strongest option:

| Service | Max Quality |
|---|---|
| Qobuz | 24-bit/192 kHz FLAC |
| Tidal | 16-bit FLAC / MQA |
| Deezer | 16-bit FLAC (HiFi) |
| SoundCloud | Lossy |

Features: CLI-based search, async downloads, SQLite deduplication, configurable YAML config.

**[OrpheusDL](https://github.com/OrfiTeam/OrpheusDL)** takes a modular plugin approach, including a notable JioSaavn module relevant for South Asian content.

### Dead/Risky Tools

- **Deemix** — effectively dead since 2022
- **Tidal-Media-Downloader** — stopped getting auth codes as of October 2025
- **Votify** — downloads from Spotify at 256 kbps AAC with Premium cookies, but carries account suspension risk

### Cross-Provider Fallback Logic

No existing tool automatically searches across all providers and picks highest quality. This requires custom logic:

```
For each new track from ytmusicapi:
  Search Qobuz → Tidal → Deezer via streamrip
  Fall back to YouTube Music via yt-dlp
```

The hard part is search matching — artist/title normalization across services, especially for non-Latin scripts.

---

## 3. Metadata Tagging

For Pakistani/South Asian music largely absent from MusicBrainz, the strategy must be: **preserve YouTube Music metadata first, attempt matching second, fall back gracefully always**.

### yt-dlp Metadata

`--embed-metadata` writes title, artist, album, upload date, and description from YouTube Music into the file.

**Critical gaps:**

- Track numbers are often missing or wrong
- "date" is the upload date, not release date
- Genre is never extracted
- Album artist isn't mapped

Always use `--write-info-json` to save a complete `.info.json` sidecar — this preserves every field for later enrichment.

### beets Configuration

[beets](https://github.com/beetbox/beets) is the library management backbone. Key feature: `quiet_fallback: asis` — when auto-tagging finds no MusicBrainz match, it imports files with existing tags intact instead of skipping them.

```yaml
import:
  write: yes
  copy: yes
  quiet_fallback: asis    # Import as-is when no match found
  log: ~/import.log
  languages: ['en', 'ur', 'hi']

plugins: discogs chroma fromfilename fetchart embedart lastgenre plexupdate

match:
  preferred:
    countries: ['PK', 'IN', 'US', 'GB']

musicbrainz:
  data_source_mismatch_penalty: 0.0
discogs:
  data_source_mismatch_penalty: 0.0
```

Discogs frequently has better South Asian coverage than MusicBrainz, especially for physical releases. Setting `data_source_mismatch_penalty: 0.0` for both sources lets beets treat Discogs matches equally.

**Plugins:**

- `fromfilename` — parses artist/title from filenames when tags are empty
- `chroma` — AcoustID fingerprinting (low South Asian coverage in fingerprint DB)

### mutagen Post-Processing

[mutagen](https://github.com/quodlibet/mutagen) handles all major formats (MP3, FLAC, M4A, Opus) with full Unicode support — critical for Urdu/Hindi/Arabic script.

A post-processing script to fill missing tags from `.info.json` sidecars:

```python
from mutagen import File
import json, glob, os

for json_path in glob.glob("**/*.info.json", recursive=True):
    info = json.load(open(json_path))
    base = json_path.replace('.info.json', '')
    for ext in ['.opus', '.m4a', '.mp3', '.flac']:
        if os.path.exists(base + ext):
            audio = File(base + ext, easy=True)
            if not audio.get('title'):
                audio['title'] = [info.get('track') or info.get('title')]
            if not audio.get('artist'):
                audio['artist'] = [info.get('artist') or info.get('uploader')]
            audio.save()
```

### Supplementary Sources

- **musicbrainzngs** — Lucene-powered fuzzy matching via `search_recordings(artist=..., recording=..., strict=False)`. Set confidence threshold ≥ 80, fall back to YouTube metadata below it.
- **Spotify API via spotipy** — Pakistani music has reasonable Spotify Pakistan coverage; provides album art, ISRCs, genres, and accurate release dates.

---

## 4. MusicBrainz Contribution

### The Core Constraint

The MusicBrainz `ws/2` API is essentially **read-only for entity creation**. You can search, look up, and browse all entities, but you cannot create new artists, releases, or recordings via the API. The only writable operations are submitting user tags, ratings, ISRCs, and barcodes for existing entities. A full edit API has been requested since at least 2018 (ticket MBS-211) but remains unimplemented.

### Seeding

Seeding is the closest thing to programmatic submission. You construct a POST request to `https://musicbrainz.org/release/add` with form parameters encoding the full release — a human must still review and click Submit. Key parameters: `name`, `artist_credit.names.0.artist.name`, `mediums.0.track.0.name`, `mediums.0.track.0.length` (milliseconds), `events.0.date.year`.

### Recommended Tools

- **[Harmony](https://harmony.pulsewidth.org.uk)** ([GitHub](https://github.com/kellnerd/harmony)) — aggregates metadata from Deezer, Spotify, Apple Music, and iTunes, harmonizes it, and seeds the MB release editor. Officially endorsed by the MusicBrainz community.
- **[yambs](https://codeberg.org/derat/yambs)** — seeds MusicBrainz edits from CSV/TSV files, supports artist/recording/release entity types, can open seed URLs directly in your browser or serve them from a local webpage.
- **[murdos/musicbrainz-userscripts](https://github.com/murdos/musicbrainz-userscripts)** — largest collection of importers for Bandcamp, Deezer, Discogs, Qobuz, and more. No dedicated YouTube Music → MusicBrainz importer exists yet.

### Bot-Level Automation

Bots must simulate the web UI by POSTing to internal form endpoints with session cookies. Bot accounts require approval, must be open-sourced, and are limited to 1,000 edits/day and 2,500 concurrent open edits. Additive edits (new artists, new releases) are typically auto-applied immediately without voting.

---

## 5. Local LLM Usage

### Where LLMs Help

| Task | Notes |
|---|---|
| Metadata completeness audit | Feed tag dumps from mutagen/ffprobe; flag missing artist, album, track number, genre, or album art |
| Encoding issue detection | Spot mojibake (garbled Unicode) and inconsistent transliteration within a discography |
| Non-Latin romanization | Urdu → Roman Urdu, Devanagari → romanized Hindi, Arabic script transliteration. Rule-based alternative: [uroman](https://github.com/isi-nlp/uroman) |
| Artist name normalization | "Nusrat Fateh Ali Khan" vs "Ustad Nusrat Fateh Ali Khan" — LLMs handle these judgment calls |

**Model recommendation:** Llama 3.1 8B via Ollama — fits in 12 GB VRAM at Q4_K_M quantization (~5–6 GB).

### Where LLMs Don't Help

**Audio quality verification** — deterministic tools vastly outperform LLMs:

- **FLAC Detective** (`pip install flac-detective`) — 11-rule scoring system classifying files as `AUTHENTIC`, `WARNING`, `SUSPICIOUS`, or `FAKE_CERTAIN`
- **librosa** — `librosa.feature.spectral_rolloff(y, sr, roll_percent=0.99)` estimates the effective frequency ceiling (genuine 16-bit/44.1 kHz FLAC shows content to ~22 kHz; 128 kbps MP3 transcoded to FLAC cuts off at ~16 kHz)
- **SoX** — `sox input.flac -n spectrogram -o output.png`
- **ffmpeg** — `ffmpeg -i input.flac -lavfi showspectrumpic=s=960x540 spectrogram.png`

> Vision-based spectrogram analysis with LLaVA 7B adds complexity with no advantage over FLAC Detective's deterministic scoring.

---

## 6. Plex Library Structure

### Expected Hierarchy

```
/Music/ArtistName/AlbumName/TrackNumber - TrackName.ext
```

- Compilations must use `"Various Artists"` as album artist
- Multi-disc: encode disc number in track number (101, 102, 201...) or use proper disc number tags (simple integers, not "1/2")
- Local artwork: `cover.jpg` per album folder, `artist-poster.jpg` per artist folder

### beets Path Configuration

```yaml
directory: /mnt/nas/music
paths:
  default: $albumartist/$album%aunique{}/$disc$track $title
  singleton: Non-Album/$artist/$title
  comp: Various Artists/$album%aunique{}/$disc$track $title
```

### Plugins

- **`plexupdate`** (built-in) — triggers a Plex library scan after every import
- **[beets-plexsync](https://github.com/arsaboo/beets-plexsync)** (third-party) — syncs play counts and ratings back to beets, offers AI-powered playlist generation via OpenAI-compatible APIs (works with local Ollama)

### Plexamp Sonic Analysis

Plexamp's sonic analysis uses a neural network to extract ~50 sonic parameters per track, enabling:

- Sonically Similar recommendations
- Track/Album Radio
- Sonic Adventure (gradient playlists between two tracks)
- Auto-generated mixes

**Requirements:** Plex Pass, x86/x86-64 CPU (no ARM except Apple Silicon via Rosetta). Can take hours for large libraries. Enable "Sonic analysis" and "Analyze audio tracks for loudness" in Plex server settings.

---

## 7. Orchestration

Three approaches ranked by weight:

### Option A: Huey + Redis (Recommended Minimal, ~50 MB RAM)

Python-native task queue with built-in periodic scheduling and retry. Redis is the only dependency.

```python
from huey import RedisHuey, crontab

huey = RedisHuey()

@huey.periodic_task(crontab(minute='*/30'))
def sync_youtube_music():
    new_tracks = poll_liked_songs()  # ytmusicapi
    for track in new_tracks:
        download_and_tag.schedule(args=(track,))

@huey.task(retries=3, retry_delay=300)
def download_and_tag(track):
    download(track)   # yt-dlp or streamrip
    tag(track)        # beets/mutagen
    notify(track)     # Discord webhook
```

### Option B: n8n (~300 MB RAM)

Self-hosted workflow automation with a web UI, built-in cron triggers, execution history, and 400+ integrations. Can execute Python scripts via Code nodes or shell commands. Deploy as a single Docker container. Ideal for visual pipeline monitoring without tailing logs.

### Option C: Plain cron (Absolute Minimum)

Zero dependencies. A Python script on a `*/30 * * * *` crontab. Must code your own retry logic, logging, and notifications. Works perfectly in an unprivileged Proxmox LXC.

### Avoid

Airflow (requires scheduler + webserver + PostgreSQL, minimum 4 GB RAM), Dagster, Temporal, and Celery are all overkill for this scale. Prefect is viable but adds more abstraction than needed.

### Proxmox LXC Deployment

- Huey/cron: works in standard unprivileged containers
- n8n via Docker: requires privileged LXC or `features: nesting=1`
- Mount Unraid NAS via NFS into the container for the music library
- Allocate 1–2 CPU cores and 512 MB–1 GB RAM

---

## 8. Existing Projects

| Project | Status | Notes |
|---|---|---|
| [Lidarr](https://github.com/Lidarr/Lidarr) | Active | 100% MusicBrainz-dependent. If an artist/album isn't in MB, Lidarr cannot see it. Album-centric only. |
| [Tubifarry](https://github.com/TypNull/Tubifarry) | Active | Lidarr plugin adding YouTube as source + Discogs/Deezer/Last.fm metadata. Fragile due to YouTube API changes. |
| Lidarr-on-Steroids | Active | Bundles Lidarr with Deemix for Deezer. Requires Deezer Premium + expiring ARL tokens. |
| [yubal](https://github.com/guillevc/yubal) | Active (195 stars) | Purpose-built YTM → library: ytmusicapi + yt-dlp + Spotify metadata, Docker deployment. |
| [SoulSync](https://github.com/Nezreka/SoulSync) | Active | Most ambitious: ~100k lines integrating Spotify, Tidal, YouTube, Soulseek, MusicBrainz, AcoustID, ListenBrainz, Plex/Jellyfin/Navidrome. |
| [slskd](https://github.com/slskd/slskd) | Active (2.2k stars) | Modern self-hosted Soulseek client with REST API. Often has obscure/regional music unavailable elsewhere. |
| Headphones | Dead | Not recommended. |

---

## 9. Recommended Architecture

The pipeline divides into five stages, each with a primary tool and fallback:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. POLL     │───▶│  2. DOWNLOAD │───▶│  3. TAG      │───▶│  4. ORGANIZE │───▶│  5. SERVE    │
│  ytmusicapi  │    │  streamrip   │    │  beets       │    │  beets paths │    │  Plex/       │
│  SQLite diff │    │  → yt-dlp    │    │  → mutagen   │    │  → NAS       │    │  Plexamp     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
        │                                      │
   Huey/n8n                              LLM QA pass
   (orchestrator)                        (Llama 3.1 8B)
```

| Stage | Action |
|---|---|
| **1. Poll** | Huey periodic task runs `get_liked_songs()` every 30 min, diffs against SQLite, queues new `videoId` entries |
| **2. Download** | Search Qobuz/Tidal/Deezer via streamrip for lossless; fall back to yt-dlp. Always save `.info.json` sidecars. |
| **3. Tag** | Run `beet import -q` with `quiet_fallback: asis`. Post-process with mutagen to fill gaps from `.info.json`. |
| **4. Organize** | beets moves files to `$albumartist/$album/$disc$track $title` on NAS mount, triggers Plex scan via `plexupdate`. |
| **5. Serve** | Plexamp with sonic analysis enabled. |

An optional **LLM QA pass** after Stage 3 feeds tag dumps to Llama 3.1 8B via Ollama, flagging missing fields, encoding issues, and inconsistent transliteration.

**Infrastructure:** Single Proxmox LXC with 1–2 cores and 1 GB RAM (plus GPU passthrough for the LLM if desired).

---

## 10. MusicBrainz Submission Strategies

For files that are verified, correctly-tagged master copies, there are four contribution tiers with different automation levels.

### Tier 1: Fully Automated API Submission

For records that **already exist** in MusicBrainz:

**ISRCs** (most valuable — machine-verifiable identifiers):

```python
musicbrainzngs.submit_isrcs({recording_mbid: [isrc1, isrc2]})
```

**Barcodes:**

```python
musicbrainzngs.submit_barcodes({release_mbid: barcode_string})
```

**Tags/genres** (Pakistani/South Asian genre tags are systematically missing from MB):

```python
musicbrainzngs.submit_tags({entity_id: [tag1, tag2]})
```

A Python script can scan your library, extract ISRCs via mutagen, look up the recording by artist+title in MB, confirm a match above a confidence threshold, then submit in batches — fully headless.

### Tier 2: AcoustID Fingerprinting (Semi-Automated, Extremely High Value)

The highest-leverage contribution for recordings that exist in MB but are unfingerprinted. Every fingerprint added makes the database more useful for the next person identifying an obscure track.

```python
import acoustid
import musicbrainzngs

# Generate fingerprint from the audio file
duration, fingerprint = acoustid.fingerprint_file("song.flac")

# Submit to AcoustID, linked to the MB recording MBID
acoustid.submit(
    apikey=YOUR_ACOUSTID_KEY,
    fingerprints=[{
        'duration': int(duration),
        'fingerprint': fingerprint,
        'mbid': 'the-recording-mbid-from-file-tags',
    }]
)
```

Completely headless — no browser involved. The AcoustID server clusters similar fingerprints together, so your submission strengthens existing clusters.

**Workflow:** For every file tagged with an MBID (by beets or manually), run this fingerprinting pass. Files without MBIDs can still have fingerprints submitted with title/artist/duration metadata.

### Tier 3: Seeded Browser Submission (One Human Click per Release)

For **new content that doesn't exist in MB yet** — new artists, new releases, new recordings.

- **New artists:** GET to `https://musicbrainz.org/artist/create?edit-artist.name=My+Name` — can seed type, gender, area, IPI/ISNI codes, begin/end dates, relationships, and external URLs
- **New releases:** POST to `https://musicbrainz.org/release/add` — can seed release name, type, status, language (ISO 639-3, e.g., `urd` for Urdu), script (e.g., `Arab` for Arabic), packaging, barcode, release events, labels, artist credits, and complete tracklist with durations in milliseconds

**Tool: [yambs](https://codeberg.org/derat/yambs)** — seeds MusicBrainz edits from CSV/TSV, supports multiple entity types, can open seed URLs directly in your browser.

**Practical pipeline stage for verified files:**

```
For each verified file:
  1. Search MB: does recording exist? (by ISRC if present, then artist+title fuzzy match)

  IF MATCH FOUND (score ≥ 80):
    - Submit AcoustID fingerprint (fully automated)
    - Submit any ISRCs from file tags (fully automated)
    - Submit genre tags (fully automated)
    - Store MBID in file tags via mutagen

  IF NO MATCH (recording/release doesn't exist in MB):
    - Extract structured data from tags + LLM normalization
    - Check if artist exists → generate artist seed URL if not
    - Generate release seed POST body for the full album
    - Queue in a "pending MB submissions" local web UI
    - When you click "Open in MB", it POSTs the seed and opens the browser
    - After you submit, store the returned MBID in your local DB
```

> **Label tip:** Pakistani music releases often cluster around the same major labels (EMI Pakistan, Eros, T-Series, HMV Pakistan). Find/create those labels once and reuse their MBIDs in all subsequent release seeds.

The **"pending submissions" queue** is important — a simple local Flask/FastAPI page listing unsubmitted releases with a one-click "Seed this release" button keeps it manageable for batching MB editing sessions.

### Tier 4: LLM-Assisted Submission Data Generation

Your local Llama model normalizes messy FLAC tags into the structured data MB expects (specific field formats, language codes, script codes, relationship types).

**Example prompt:**

```
Given these audio file tags:
  Artist: "Nusrat Fateh Ali Khan"
  Album: "Mustt Mustt"
  Year: 1990
  Label: "Real World Records"
  Tracks: [...]

Generate MusicBrainz release editor seed parameters:
- Correct ISO 639-3 language code (likely Urdu/Punjabi)
- ISO 15924 script code (Arab for Urdu, Guru for Punjabi, or Latn if romanized)
- Artist sort name (MB format: "Last, First" or "Khan, Nusrat Fateh Ali")
- Release country ISO code
- Whether artist type is "Person" or "Group"
- Any missing data flagged for manual review
```

**Where LLMs excel in this context:**

- Disambiguating Punjabi vs Urdu vs Hindi script choices
- Generating correct sort names for South Asian artists (Pakistani names often don't follow Western first/last conventions)
- Identifying whether something is a soundtrack vs album vs EP vs single
- Normalizing inconsistent label names to their canonical form
- Auto-generating edit notes (the MB community cares about these — a note like *"Data from verified FLAC download, EMI Pakistan pressing, tags confirmed against physical release"* significantly reduces the chance of edits being voted down)
