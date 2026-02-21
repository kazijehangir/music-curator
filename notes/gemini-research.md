# Automated Audiophile Curation: A Technical Blueprint for Preserving Pakistani Musical Heritage

## 1. Introduction: The Crisis of Metadata in South Asian Digital Archiving

The digitization of global music culture has not been evenly distributed. While Western popular music benefits from robust, standardized metadata infrastructures—underpinned by universal identifiers like ISRCs (International Standard Recording Codes) and comprehensive databases like MusicBrainz and Discogs—South Asian musical heritage, particularly that of Pakistan, faces a profound crisis of discoverability and provenance. For the audiophile archivist, this presents a dual challenge: acquiring high-fidelity assets in a landscape rife with lossy upscales, and rectifying a metadata ecosystem plagued by inconsistent transliteration, fragmentation, and neglect.

This report outlines a comprehensive technical architecture for an automated, self-healing music curation pipeline. It is designed not merely to consume content, but to actively actively rehabilitate it. By leveraging a distributed hardware infrastructure—comprising Proxmox virtualization, Unraid storage arrays, and high-performance GPU computing—we propose a system that monitors streaming behaviors, acquires lossless audio, validates signal integrity through spectral analysis, and employs Large Language Models (LLMs) to normalize complex Urdu/Hindi nomenclature.

Crucially, this architecture treats the local library as a staging ground for global contribution. We explore sophisticated mechanisms to feed cleaned, verified metadata back into the MusicBrainz ecosystem, transforming a personal Plexamp library into a node of preservation for the broader community. This shift from passive consumption to "active archival" requires a rigorous integration of Python automation, containerized microservices, and AI-driven semantic analysis.

## 2. Theoretical Framework: The Challenges of Pakistani Music Metadata

To architect a solution, one must first understand the specific entropy of the dataset. Pakistani music metadata suffers from three distinct entropy vectors that standard tools (like MusicBrainz Picard's default clustering) fail to address effectively.

### 2.1. The Transliteration Variance Problem

Unlike Western languages that share the Latin script, Urdu—the lingua franca of Pakistani music—utilizes the Perso-Arabic script (Nastaliq). Digital platforms, however, predominantly rely on Romanized (transliterated) metadata. This process is non-standardized, leading to massive variance in artist and track naming.

* **Phonetic Ambiguity:** The name "Nusrat" might appear as "Nasrat" or "Nusrut". The honorific "Khan" is occasionally stylized as "Khaan".
* **Compound Naming Conventions:** A Qawwali group might be credited as "Rahat Fateh Ali Khan & Party", "Rahat Fateh Ali Khan Group", or simply "Rahat Fateh Ali Khan".
* **Script Normalization:** Standardizing these variations requires more than simple string matching; it requires semantic understanding of the underlying Urdu phonology. Libraries like urduhack [1] and LughaatNLP [2] provide computational linguistic tools to normalize Urdu text, stripping diacritics and normalizing unicode characters (e.g., merging differing Unicode representations of 'He' or 'Te'). Integrating these logic gates into a curation pipeline is essential for deduplication.

### 2.2. The Upscale Epidemic in Digital Supply Chains

The digital distribution of South Asian music in the early 2000s was often chaotic. Master tapes were frequently digitized to low-bitrate MP3s (128kbps) for bandwidth-constrained environments. As streaming services like Deezer and Tidal emerged, some aggregators simply re-encoded these lossy files into FLAC containers to meet "Hi-Fi" delivery requirements. Consequently, a file flagged as "Lossless FLAC" by a downloader may essentially be a "spectral lie"—a 128kbps MP3 inside a high-bitrate wrapper. An automated pipeline must therefore include forensic audio analysis [3] to reject these false positives before they pollute the archival library.

### 2.3. The "Singleton" Release Culture

Much of modern Pakistani pop and hip-hop (e.g., Young Stunners, Hasan Raheem) is released as singles directly to YouTube or Soundcloud before hitting DSPs (Digital Service Providers). MusicBrainz, which favors album-centric organization, often lacks entries for these singles. The pipeline must therefore support a "Singleton" workflow that can organize tracks without a parent album entity while simultaneously preparing the data to seed a new release entry on MusicBrainz. [4]

## 3. Infrastructure Architecture & Hardware Topology

The user's hardware portfolio offers a diverse set of capabilities. A monolithic script running on a single machine would be inefficient and fragile. Instead, we propose a Distributed Microservices Architecture, decoupling the workflow into specialized nodes that communicate via RESTful APIs and network-attached storage (NFS/SMB).

### 3.1. Node Responsibilities and Service Distribution

| Hardware Node | Component Role | Assigned Microservices & Responsibilities |
| :--- | :--- | :--- |
| **Proxmox Host** | Orchestration Plane | **LXC Container (Ubuntu):** Hosting the "Master Controller" (Python/n8n) [5]. This node manages the state database (Redis/SQLite), handles API polling, and triggers workflows on other nodes. It acts as the traffic cop. |
| **Unraid Server** | Storage & Media | **Docker Containers:** beets (Library Management) [6], Plex Media Server (Playback), PostgreSQL (Metadata Index). <br> **Storage:** Exports `/mnt/user/music` (Library) and `/mnt/user/downloads` (Ingest) via NFS. |
| **Windows PC** | Compute Node | **GPU Worker:** Leveraging the RTX 3080 Ti for AI workloads. Hosts Ollama [7] for metadata cleaning and potentially fat_llama [8] or penthy [9] for neural-network-based audio upscale detection. |
| **MacBook** | Interface & Verification | **Client:** Used for "Human-in-the-Loop" verification. Runs Playwright scripts [10] in "headed" mode to automate the final click-through for MusicBrainz submissions that require visual confirmation. |

### 3.2. The "Windows-as-an-API" Strategy

Running heavy AI inference (LLMs, neural audio analysis) on Linux containers in Proxmox is possible but often complicated by GPU passthrough requirements (IOMMU groups, driver isolation) [11]. Given the powerful RTX 3080 Ti resides in the Windows PC, the most robust architectural decision is to treat the Windows machine not as a script runner, but as an on-demand Compute API.

By installing a lightweight web server (FastAPI or Flask) [12] on the Windows machine, we can expose endpoints like `/analyze_audio` and `/clean_metadata`. The Linux-based Orchestrator on Proxmox can simply send an HTTP POST request with the file path (accessible via network share) or metadata payload. The Windows machine processes the request using its GPU and returns the result JSON. This approach [13] circumvents the fragility of SSHing into Windows or configuring WinRM [14] for interactive tasks and allows the Windows PC to remain a usable workstation.

### 3.3. Storage Hierarchy and Path Mapping

To ensure atomic file operations and prevent race conditions, the Unraid server must export a high-performance NFS share. The orchestration node (Proxmox) and the Compute Node (Windows) must have identical or mapped visibility to the staging area.

* **Ingest Zone:** `/mnt/user/data/ingest/` - Where streamrip dumps raw downloads.
* **Processing Zone:** `/mnt/user/data/processing/` - Where files are moved during spectral analysis and tagging.
* **Library Zone:** `/mnt/user/media/music/` - The final destination for Beets-processed, Plex-ready files.

## 4. Phase 1: The Acquisition & Deduplication Engine

The pipeline begins with intelligent monitoring. We aim to mirror the "Liked Songs" playlist from YouTube Music, which serves as the user's primary discovery vector, into a local lossless archive.

### 4.1. YouTube Music Polling (ytmusicapi)

The `ytmusicapi` library [15] is the de facto standard for interacting with YouTube Music without the limitations of the official Google API.

**Implementation Strategy:**

* **Authentication:** The browser-based authentication flow (copying request headers) generates a `headers_auth.json` file [16]. This file is static and should be mounted as a secret into the Proxmox LXC container.
* **State Tracking:** A simple cron job cannot just download "new" songs because tracks may be reordered or removed. The script must maintain a local SQLite database table: `tracked_songs (video_id PRIMARY KEY, title, artist, status, local_path)`.
* **Polling Logic:** Every 6 hours, the script fetches the LM (Liked Music) playlist using `yt.get_liked_songs(limit=None)` [17]. It iterates through the results:
  * If `videoId` exists in SQLite: SKIP.
  * If `videoId` is new: QUEUE for acquisition.

### 4.2. Intelligent Deduplication: The "Already Exists" Check

Before attempting a download, the system must verify if the song exists in the Unraid library. This is non-trivial due to the transliteration variance described in Section 2.1. A song titled "Tere Bin" on YouTube might exist as "Tere Bina" in the local FLAC library.

**Multi-Layer Verification Protocol:**

* **Beets Database Query:** The most reliable check is against the beets library, which contains curated metadata. The script executes a remote command or queries the Beets SQLite database directly [18].
  * Query: `beet ls artist:"<Artist>" title:"<Title>"`
* **PlexAPI Fallback:** If Beets is ambiguous, query Plex [19]. Plex's sonic analysis features can sometimes link tracks even with metadata disparities.
  * Method: `plex.library.section('Music').search(title='Song Name', artist='Artist Name')`
* **Fuzzy Logic Matching:** If exact matches fail, apply fuzzy string matching using `thefuzz` (formerly fuzzywuzzy) [20].
  * **Thresholding:** Calculate the `token_sort_ratio`. If ratio > 85 for the title AND ratio > 90 for the artist, treat it as a potential duplicate and flag for human review rather than auto-downloading. This prevents re-downloading "Nusrat Fateh Ali Khan" tracks simply because YouTube lists them as "NFAK".

### 4.3. The High-Fidelity Downloader (streamrip)

Once a track is confirmed as missing, the pipeline hands off to `streamrip` [21], a powerful CLI tool capable of interacting with Qobuz, Tidal, and Deezer.

**Source Prioritization Logic:** The configuration file (`config.toml`) for streamrip should be rigorously set to prioritize audio fidelity [22]:

1. **Qobuz:** Priority 1. Offers true 24-bit/96kHz+ Hi-Res capabilities and generally cleaner masters for World Music genres.
2. **Tidal:** Priority 2. Excellent catalog, but the script must be configured to handle MQA (Master Quality Authenticated) files carefully, ensuring the system can decode or preserve the fold-down correctly.
3. **Deezer:** Priority 3. Reliable 16-bit/44.1kHz (CD Quality). Essential for obscure Pakistani tracks that may not be on high-res tiers.

**Command Execution:**

The Python controller constructs a search command based on the YouTube metadata.

```bash
rip search --source qobuz --type track --quality 3 "Artist - Title"
```

**Note:** The script must parse the streamrip output. If multiple results are returned (e.g., Remixes, Live versions), the script compares the Duration metadata. A delta of >5 seconds suggests a different version, triggering a fallback or a "Manual Review" flag.

## 5. Phase 2: Audio Forensic Analysis (The Quality Gate)

Downloading a file labeled "FLAC" is only the first step. The "Quality Gate" ensures that the file is truly lossless and not an upscaled MP3.

### 5.1. The Upscaling Detection Engine

We will employ a two-tiered analysis strategy running on the Windows Compute Node (via the API wrapper) to leverage the GPU where possible.

* **Tier 1: Algorithmic Verification (redoflacs / auCDtect):** `redoflacs` [3] is a robust bash script wrapper around the auCDtect algorithm. It analyzes the statistical properties of the audio stream to determine if high-frequency content is consistent with lossless encoding.
  * **Workflow:** The Proxmox orchestrator executes `redoflacs` on the NFS mount.
  * **Pass Condition:** Confidence > 95% CDDA.
  * **Fail Condition:** MPEG detected or Confidence < 95%.

* **Tier 2: Neural Network Verification (penthy / fat_llama):** For files that fail Tier 1 or are ambiguous (common with older Pakistani analog transfers), we utilize the RTX 3080 Ti. Tools like `penthy` [9] utilize Convolutional Neural Networks (CNNs) trained on spectrogram images to detect compression artifacts that algorithmic tools miss.
  * **Execution:** The file path is passed to the Windows API. The Windows machine runs the inference using tensorflow or pytorch.
  * **Benefit:** This is highly effective for detecting "Youtube-rips" that have been upconverted, a frequent issue with Pakistani music distributed via non-official channels.

### 5.2. Handling Rejection

Files that fail validation are not deleted. They are moved to a `_Review/Upscales` folder on Unraid. A notification is sent (via n8n to Discord/Telegram) containing the auCDtect report and a generated spectrogram image [23] created via `sox`. This allows the user to make a subjective decision—sometimes a 320kbps upscale is the only existing copy of a rare 1970s Ghazal.

## 6. Phase 3: Semantic Metadata Enrichment (The Intelligence Layer)

This phase addresses the "Pakistani Music" context problem. Standard taggers (MusicBrainz Picard) rely on existing database entries. If the data is missing or messy, Picard fails. We introduce a Local LLM Metadata Cleaner to synthesize clean metadata from messy inputs.

### 6.1. The LLM Configuration (Windows GPU)

We utilize Ollama [7] hosting a quantized version of Llama 3 or Mistral. These models have sufficient general knowledge to understand South Asian naming conventions if prompted correctly.

**The "Windows-as-API" Implementation:**

A Python script using FastAPI runs on the Windows machine. It exposes a POST endpoint.

**System Prompt Engineering:** The prompt is the engine of this phase. It must be strictly engineered to enforce JSON schemas [24] and handle transliteration rules.

**System Prompt:**

```text
"You are an expert music archivist specializing in South Asian and Pakistani music. Your task is to clean, standardize, and enrich metadata for music tracks.

Rules:
Transliteration: Standardize Roman Urdu names to their most common academic transliteration. Use 'Khan' not 'Khaan'. Use 'Fateh' not 'Fatteh'. Normalize 'Rahat Fateh Ali Khan' to 'Rahat Fateh Ali Khan'.
Splitting: If the input string is 'Artist - Title (feat. X)', extract 'X' as a 'featured_artist'.
Genre: Infer specific genres. If the title contains 'Qawwali', set genre to 'Qawwali'. If 'Ghazal', set to 'Ghazal'. Do not use generic 'World' tags.

Output: Return ONLY a JSON object with keys: artist, title, album, genre, featured_artists (list)."
```

### 6.2. Python Wrapper and Validation

The Python script calling Ollama must use `pydantic` [25] to validate the returned JSON. If the LLM returns a hallucinated format, pydantic will raise a validation error, triggering a retry with a higher temperature setting. This ensures that the metadata passed to the next stage is programmatically usable.

## 7. Phase 4: Library Organization (Beets Integration)

`beets` [26] is the library management system that enforces order. It runs on Unraid (via Docker) and acts as the gatekeeper to the final Plex library.

### 7.1. Beets Configuration (config.yaml)

For this pipeline, beets must be configured for rigid structure and semi-automated import.

**Plugins:**

* `fetchart` & `embedart`: For cover art.
* `lyrics`: Essential for Urdu poetry.
* `scrub`: To remove existing garbage tags (e.g., "Downloaded from X site").
* `replaygain`: For volume normalization in Plexamp.
* `edit`: To manually intervene if necessary.
* `mbsync` [27]: Crucial for the feedback loop (discussed in Phase 5).

**Matching Config:**
We set strict matching thresholds to prevent false positives.

```yaml
match:
  strong_rec_thresh: 0.04
  max_rec:
    missing_tracks: medium
    unmatched_tracks: medium
```

### 7.2. The "Singleton" Workflow for Unmatched Tracks

Tracks processed by the LLM that are not on MusicBrainz will fail the standard beet import. We must run beet import with the `--singleton` flag for these specific files. We will use a custom field `mb_status` set to `pending` for these tracks. This flag serves as a marker for the "Golden Loop"—indicating that this track needs to be submitted to MusicBrainz.

## 8. Phase 5: The "Golden Loop" – Automated MusicBrainz Contribution

This is the most ambitious component: closing the data loop by submitting the high-quality, LLM-cleaned metadata back to MusicBrainz. This transforms the user from a leecher to a seeder of metadata.

### 8.1. The Anti-Bot Constraint

MusicBrainz has strict policies against fully autonomous bots creating releases [28]. "Fire-and-forget" scripts that POST data without review are frequently banned. Therefore, our architecture implements Programmatic Seeding with Human Verification.

### 8.2. Strategy A: Release Editor Seeding (The Safe Route)

Instead of using the API to write to the database, we use the `release/add` endpoint to pre-fill the editing form [30].

**The Seeding Generator Script:**
A Python script on the Proxmox orchestrator reads the metadata of files marked `mb_status: pending`. It maps this data to the specific query parameters accepted by the MusicBrainz Release Editor.

**Mapping Logic:**

* `name` -> Cleaned Album Title (from LLM)
* `artist_credit.names.0.name` -> Cleaned Artist Name
* `events.0.country` -> "PK" (Pakistan)
* `mediums.0.track.0.name` -> Track Title
* `mediums.0.track.0.length` -> Duration (extracted via `ffprobe` in milliseconds)

The script generates a URL (e.g., `musicbrainz.org/release/add?name=...`). This URL is pushed to a dashboard or a notification queue. When the user has time, they click the link on their MacBook. The MusicBrainz editor opens with all data pre-filled. The user visually verifies the data (checking for transliteration errors the LLM might have missed) and clicks "Enter Edit". This reduces a 10-minute manual entry process to 30 seconds of verification.

### 8.3. Strategy B: Browser Automation (The "Power User" Route)

For a higher degree of automation, we can employ Playwright [10] or Selenium [32] running on the MacBook or in a "headed" container.

**The Workflow:**

* **Script:** The Python script uses musicbrainz-bot concepts [29].
* **Action:** It launches a browser instance, logs into MusicBrainz, navigates to the seeding URL, and effectively "stages" the submission.
* **Pause:** The script pauses execution and waits for user input. It can take a screenshot of the filled form and send it to the user.
* **Confirmation:** The user reviews the screenshot. If approved, the user sends a "GO" signal (via API or simple keypress), and the script clicks the final "Submit" button using the appropriate CSS selector [33].

**Warning:** This method navigates the grey area of MusicBrainz's bot policy. It is imperative that this is rate-limited (e.g., 1 release every 10 minutes) and always includes a human verification step to avoid "bot gone wild" scenarios where hundreds of duplicate or erroneous releases are created.

### 8.4. Closing the Loop with mbsync

Once the release is live on MusicBrainz:

1. The local beets library still treats the file as "unmatched" or "singleton".
2. After 24 hours (allowing for replication), a scheduled task runs `beet mbsync` [27] on the Unraid server.
3. Beets queries MusicBrainz, finds the release you just added (matching by the exact track lengths and titles you seeded), and updates the local file tags with the official MusicBrainz ID (MBID).
4. Plexamp rescans the file. Because it now has an MBID, Plex matches it against its sonic analysis database, unlocking features like "Sonically Similar" tracks and "Guest Mixes".

## 9. Implementation Roadmap

* **Phase 1: Foundation (Days 1-7)**
  * **Proxmox:** Deploy Ubuntu LXC container (`music-orchestrator`). Install Python 3.11, `ytmusicapi`, `ffmpeg`, `sox`.
  * **Unraid:** Configure NFS shares for `/ingest` and `/library`. Ensure permissions are set for the Proxmox container user.
  * **Windows:** Install Python, Ollama (with Llama 3), and setup the `flask-llm-wrapper`. Verify Proxmox can curl the Windows endpoint.

* **Phase 2: Acquisition & Forensics (Days 8-14)**
  * Configure `streamrip` with `config.toml` set to `[qobuz, tidal, deezer]`.
  * Write `ytm_monitor.py` to poll the Liked playlist and update the SQLite history db.
  * Implement `audio_verifier.py` on Proxmox to run `redoflacs` on downloads. Set up the notification webhook for failed checks.

* **Phase 3: The Intelligence Engine (Days 15-21)**
  * Develop the System Prompt for the LLM. Test with complex Pakistani titles (e.g., "Coke Studio Season 14 - Kana Yaari").
  * Refine transliteration rules in the prompt based on output analysis.
  * Create the Python script that orchestrates the flow: Download -> Verify -> POST to Windows API -> Parse JSON.

* **Phase 4: Integration & Contribution (Days 22-30)**
  * Configure beets on Unraid with `mbsync` and `edit` plugins.
  * Develop the `seeding_generator.py` module. Test generating seeding URLs for single tracks.
  * (Optional) Set up Playwright on the MacBook for "one-click" submission of seeded URLs.
  * **Final Test:** Like a new song on YouTube Music -> Watch it download -> Verify it passes validation -> See it cleaned by LLM -> Click the generated link to add to MusicBrainz -> Sync back to Plexamp.

## 10. Conclusion

This architecture represents a paradigm shift in personal media curation. It moves beyond simple file hoarding to establish a sophisticated, quality-controlled, and community-contributing archival system. By solving the specific challenges of Pakistani music metadata through local AI and programmatic seeding, the system ensures that the rich cultural heritage of the region is preserved with the fidelity and accuracy it deserves. The result is a Plexamp library that is not only a joy to listen to but a testament to the power of automated digital preservation.

---

## Appendix A: Tables and Configurations

**Table 1: Software Stack & Versions**

| Component | Software | Version/Branch | Purpose |
| :--- | :--- | :--- | :--- |
| API Wrapper | Flask/FastAPI | Latest | Exposing Windows GPU functions to network |
| LLM Inference | Ollama | > 0.1.20 | Running Llama 3 for metadata cleaning |
| Music Downloader | Streamrip | Dev Branch | Multi-source FLAC acquisition |
| Library Manager | Beets | > 1.6.0 | Tagging, organizing, and MB sync |
| Browser Auto | Playwright | Python API | Semi-automated MusicBrainz submission |
| Audio Analysis | Redoflacs | Latest | Spectrogram/upscale verification |

**Table 2: Source Prioritization Matrix**

| Provider | Priority | Format | Justification |
| :--- | :--- | :--- | :--- |
| Qobuz | 1 | FLAC (24/96+) | Best master quality, no DRM/MQA artifacts. |
| Tidal | 2 | FLAC (16/44.1) | Large catalog, fallback if Qobuz fails. |
| Deezer | 3 | FLAC (16/44.1) | Reliable CD quality, extensive World catalog. |
| YouTube | 4 | Opus/AAC | Last resort fallback (lossy) if no FLAC exists. |

## Appendix B: Concept Code - Windows LLM API (Flask)

```python
from flask import Flask, request, jsonify
import ollama

app = Flask(__name__)

@app.route('/clean_metadata', methods=['POST'])
def clean_metadata():
    data = request.json
    raw_artist = data.get('artist')
    raw_title = data.get('title')
    
    # System Prompt with Pakistani Context
    prompt = f"""
    Standardize this Pakistani music metadata. 
    Context: Fix transliteration (e.g., 'Khatak' -> 'Khattak'). 
    Input: Artist='{raw_artist}', Title='{raw_title}'.
    Output JSON keys: artist, title, album, is_ghazal (bool).
    """
    
    response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
    # Add robust JSON parsing/validation here using Pydantic
    return jsonify(response['message']['content'])

if __name__ == '__main__':
    # Listen on all interfaces to allow Proxmox connection
    app.run(host='0.0.0.0', port=5000)
```

---

## Works cited

1. **Normalization — Urduhack 1.0.3 documentation** - *Read the Docs*, accessed February 18, 2026, [https://urduhack.readthedocs.io/en/stable/reference/normalization.html](https://urduhack.readthedocs.io/en/stable/reference/normalization.html)
2. **LughaatNLP: A Powerful Urdu Language Preprocessing Library** - *GeeksforGeeks*, accessed February 18, 2026, [https://www.geeksforgeeks.org/artificial-intelligence/lughaatnlp-a-powerful-urdu-language-preprocessing-library/](https://www.geeksforgeeks.org/artificial-intelligence/lughaatnlp-a-powerful-urdu-language-preprocessing-library/)
3. **sirjaren/redoflacs**: Parallel BASH commandline FLAC compressor, verifier, organizer, analyzer, and retagger - *GitHub*, accessed February 18, 2026, [https://github.com/sirjaren/redoflacs](https://github.com/sirjaren/redoflacs)
4. **Release** - *MusicBrainz*, accessed February 18, 2026, [https://musicbrainz.org/doc/Release](https://musicbrainz.org/doc/Release)
5. **Automated music video creation & YouTube publishing with AI-generated metadata from Google Drive** | *n8n workflow template*, accessed February 18, 2026, [https://n8n.io/workflows/4848-automated-music-video-creation-and-youtube-publishing-with-ai-generated-metadata-from-google-drive/](https://n8n.io/workflows/4848-automated-music-video-creation-and-youtube-publishing-with-ai-generated-metadata-from-google-drive/)
6. **How to Use Beets for Sorting Your Music** : r/musichoarder - *Reddit*, accessed February 18, 2026, [https://www.reddit.com/r/musichoarder/comments/7vy7n7/how_to_use_beets_for_sorting_your_music/](https://www.reddit.com/r/musichoarder/comments/7vy7n7/how_to_use_beets_for_sorting_your_music/)
7. **How to Use Ollama with Docker** - *OneUptime*, accessed February 18, 2026, [https://oneuptime.com/blog/post/2026-01-28-ollama-docker/view](https://oneuptime.com/blog/post/2026-01-28-ollama-docker/view)
8. **fat_llama** is a Python package for upscaling audio files to FLAC or WAV formats using advanced audio processing techniques. - *GitHub*, accessed February 18, 2026, [https://github.com/bkraad47/fat_llama](https://github.com/bkraad47/fat_llama)
9. **gioypi/penthy**: Neural network for classification of flac compression quality (discontinued), accessed February 18, 2026, [https://github.com/gioypi/penthy](https://github.com/gioypi/penthy)
10. **Understanding Headless vs. Headed Modes in Playwright: A Guide for QA Automation Engineers / SDETs** - *Dev.to*, accessed February 18, 2026, [https://dev.to/johnnyv5g/understanding-headless-vs-headed-modes-in-playwright-a-guide-for-qa-automation-engineers-sdets-4h7e](https://dev.to/johnnyv5g/understanding-headless-vs-headed-modes-in-playwright-a-guide-for-qa-automation-engineers-sdets-4h7e)
11. **How to Enable GPU Passthrough in Proxmox VE | Full Host Setup Guide (AMD & Intel)**, accessed February 18, 2026, [https://www.youtube.com/watch?v=HDn2fjJNR7o](https://www.youtube.com/watch?v=HDn2fjJNR7o)
12. **Developing RESTful APIs with Python and Flask** | *Auth0*, accessed February 18, 2026, [https://auth0.com/blog/developing-restful-apis-with-python-and-flask/](https://auth0.com/blog/developing-restful-apis-with-python-and-flask/)
13. **Run GPU tasks remotely on Windows Server 2016 with coding** - *Infinitive Host*, accessed February 18, 2026, [https://www.infinitivehost.com/knowledge-base/run-gpu-tasks-remotely-on-windows-server-2016-with-coding/](https://www.infinitivehost.com/knowledge-base/run-gpu-tasks-remotely-on-windows-server-2016-with-coding/)
14. **Can I install WinRM on Linux for cross-platform PowerShell remoting?** - *Stack Overflow*, accessed February 18, 2026, [https://stackoverflow.com/questions/75694704/can-i-install-winrm-on-linux-for-cross-platform-powershell-remoting](https://stackoverflow.com/questions/75694704/can-i-install-winrm-on-linux-for-cross-platform-powershell-remoting)
15. **ytmusicapi: Unofficial API for YouTube Music** — ytmusicapi 1.11.5 documentation, accessed February 18, 2026, [https://ytmusicapi.readthedocs.io/](https://ytmusicapi.readthedocs.io/)
16. **diminDDL/ytmusicpltools**: A few python scripts to download liked music from ytmusic... - *GitHub*, accessed February 18, 2026, [https://github.com/diminDDL/ytmusicpltools](https://github.com/diminDDL/ytmusicpltools)
17. **ytmusicapi: An unofficial Python API client for YouTube Music** - *Reddit*, accessed February 18, 2026, [https://www.reddit.com/r/YoutubeMusic/comments/fk788q/ytmusicapi_an_unofficial_python_api_client_for/](https://www.reddit.com/r/YoutubeMusic/comments/fk788q/ytmusicapi_an_unofficial_python_api_client_for/)
18. **Library Database API - beets** - *Read the Docs*, accessed February 18, 2026, [https://beets.readthedocs.io/en/stable/dev/library.html](https://beets.readthedocs.io/en/stable/dev/library.html)
19. **Audio plexapi.audio** — Python PlexAPI documentation - *Read the Docs*, accessed February 18, 2026, [https://python-plexapi.readthedocs.io/en/latest/modules/audio.html](https://python-plexapi.readthedocs.io/en/latest/modules/audio.html)
20. **Python code to fuzzy match two files...** · *GitHub*, accessed February 18, 2026, [https://gist.github.com/claczny/83c402176b6ab2683ecb4540412c00e4](https://gist.github.com/claczny/83c402176b6ab2683ecb4540412c00e4)
21. **nathom/streamrip**: A scriptable music downloader for Qobuz, Tidal, SoundCloud, and Deezer - *GitHub*, accessed February 18, 2026, [https://github.com/nathom/streamrip](https://github.com/nathom/streamrip)
22. **streamrip 0.5.2** - *PyPI*, accessed February 18, 2026, [https://pypi.org/project/streamrip/0.5.2/](https://pypi.org/project/streamrip/0.5.2/)
23. **How to create the spectrogram of many audio files efficiently with Sox?**, accessed February 18, 2026, [https://unix.stackexchange.com/questions/200168/how-to-create-the-spectrogram-of-many-audio-files-efficiently-with-sox](https://unix.stackexchange.com/questions/200168/how-to-create-the-spectrogram-of-many-audio-files-efficiently-with-sox)
24. **Structured outputs** · *Ollama Blog*, accessed February 18, 2026, [https://ollama.com/blog/structured-outputs](https://ollama.com/blog/structured-outputs)
25. **Constraining LLMs with Structured Output: Ollama, Qwen3 & Python or Go** - *Medium*, accessed February 18, 2026, [https://medium.com/@rosgluk/constraining-llms-with-structured-output-ollama-qwen3-python-or-go-2f56ff41d720](https://medium.com/@rosgluk/constraining-llms-with-structured-output-ollama-qwen3-python-or-go-2f56ff41d720)
26. **beetbox/beets**: music library manager and MusicBrainz tagger - *GitHub*, accessed February 18, 2026, [https://github.com/beetbox/beets](https://github.com/beetbox/beets)
27. **MBSync Plugin** — beets 1.5.0 documentation, accessed February 18, 2026, [https://beets.readthedocs.io/en/v1.5.0/plugins/mbsync.html](https://beets.readthedocs.io/en/v1.5.0/plugins/mbsync.html)
28. **Any plans to add POST or edit capability for the MusicBrainz API ...**, accessed February 18, 2026, [https://community.metabrainz.org/t/any-plans-to-add-post-or-edit-capability-for-the-musicbrainz-api/747653](https://community.metabrainz.org/t/any-plans-to-add-post-or-edit-capability-for-the-musicbrainz-api/747653)
29. **Bot based on Discogs Data** - MusicBrainz - *MetaBrainz Community Discourse*, accessed February 18, 2026, [https://community.metabrainz.org/t/bot-based-on-discogs-data/669295](https://community.metabrainz.org/t/bot-based-on-discogs-data/669295)
30. **Development / Seeding / Release Editor** - *MusicBrainz*, accessed February 18, 2026, [https://musicbrainz.org/doc/Release_Editor_Seeding](https://musicbrainz.org/doc/Release_Editor_Seeding)
31. **Development / Seeding / Release Editor** - *MusicBrainz*, accessed February 18, 2026, [https://musicbrainz.org/doc/Development/Release_Editor_Seeding#Seeding_to_the_next_step](https://musicbrainz.org/doc/Development/Release_Editor_Seeding#Seeding_to_the_next_step)
32. **Harmony Assistant - Automated album-importing using Harmony and Selenium**, accessed February 18, 2026, [https://community.metabrainz.org/t/harmony-assistant-automated-album-importing-using-harmony-and-selenium/813659](https://community.metabrainz.org/t/harmony-assistant-automated-album-importing-using-harmony-and-selenium/813659)
33. **How to click a "type=submit" button in Playright** - *Stack Overflow*, accessed February 18, 2026, [https://stackoverflow.com/questions/71648929/how-to-click-a-type-submit-button-in-playright](https://stackoverflow.com/questions/71648929/how-to-click-a-type-submit-button-in-playright)
