--- 
# Prompt

Can you do a deep evaluation of these workflow proposals from previous AI brainstorming? I want you to generate a very detailed concrete plan with your recommendations for implementing this music curation workflow

---
# Response

Here is a deep evaluation of the two AI-generated workflow proposals, followed by a synthesized, concrete implementation plan that extracts the best architectural decisions from both.

### Part 1: Deep Evaluation of the Proposals

Both proposals aim to solve the same highly specific problem: the lack of standardized metadata and lossless availability for Pakistani/South Asian music. However, they take different philosophical approaches.

**1. Orchestration and Hardware**

* **Gemini** proposes a distributed microservices approach utilizing Proxmox (Orchestrator), Unraid (Storage), and a Windows PC (GPU Compute API). This is a **brilliant hardware utilization strategy**, as it avoids the nightmare of passing through a consumer GPU (RTX 3080 Ti) to Linux containers in Proxmox, instead treating Windows as a local API endpoint.
* **Claude** focuses purely on software logic, recommending **n8n** or **Huey**. n8n is highly recommended here as it provides visual logging—crucial when dealing with edge cases in messy metadata.

**2. Audio Forensics (The Quality Gate)**

* **Gemini** over-engineers this by suggesting neural networks (`penthy` or Vision LLMs) to analyze spectrograms.
* **Claude** rightly points out that this is a mistake. **Deterministic tools vastly outperform LLMs for audio analysis.** Tools like `flac-detective` or `redoflacs` using algorithmic frequency cut-off detection are faster and more accurate.

**3. Acquisition & Downloader Logic**

* **Both** correctly identify that Lidarr is useless for this niche due to its 100% reliance on MusicBrainz.
* **Both** select `ytmusicapi` for polling and `streamrip` for lossless acquisition.
* **Claude** provides a superior fallback mechanism: using `yt-dlp` to pull YouTube Music's `141 AAC (256kbps)` format, preserving the `.info.json` for metadata ingestion.

**4. MusicBrainz Contribution (The "Golden Loop")**

* **Gemini** suggests a risky browser automation strategy (Playwright) which violates MusicBrainz's bot policies and could lead to IP bans.
* **Claude** provides an absolute masterclass in MusicBrainz contribution. Its **4-Tier strategy** is the correct path: automatically submitting ISRCs/AcoustIDs via API, and using an LLM to generate Seed URLs for a human to click and review via a local Flask dashboard.

---

### Part 2: The Ultimate Concrete Implementation Plan

Based on the evaluation, here is the definitive, step-by-step blueprint for building your curation pipeline. It blends Gemini’s "Windows-as-an-API" hardware topology with Claude’s deterministic logic and tiered community contribution.

#### **The Infrastructure Stack**

* **Orchestrator (Proxmox LXC):** Hosts **n8n** (via Docker with `nesting=1`). n8n handles the cron scheduling, API logic, and Discord notifications.
* **Storage & Library (Unraid):** Hosts your media shares, **Beets** container, and **Plex Media Server**.
* **Compute Node (Windows PC):** Runs **Ollama** (hosting Llama 3.1 8B) and a lightweight Python **FastAPI** server. It acts purely as a local API for LLM queries.

#### **Phase 1: Discovery & Acquisition**

1. **Poll YouTube Music:** n8n runs a cron job every 6 hours. A Python script node uses `ytmusicapi` to fetch your "Liked Music" playlist.
2. **State Tracking:** n8n checks the `videoId` against a local SQLite database (`tracked_songs`) to ensure it hasn't been processed before.
3. **Cross-Check Beets:** Before downloading, n8n queries the Beets database. *Do not use exact string matching.* Use fuzzy matching on the Artist/Title to catch transliteration differences (e.g., "NFAK" vs "Nusrat Fateh Ali Khan").
4. **Download Waterfall:**
    * *Attempt 1 (Lossless):* Execute `streamrip` searching Qobuz, then Tidal, then Deezer.
    * *Attempt 2 (Lossy Fallback):* If `streamrip` fails, execute `yt-dlp -f 141 --embed-metadata --write-info-json` to grab the 256kbps AAC file and the raw YouTube JSON metadata.

#### **Phase 2: The Forensic Quality Gate**

Do not use AI for this step.

1. Run `flac-detective` (or a `librosa` Python script) on downloaded FLAC files to check the spectral roll-off.
2. **If PASS:** Move to Phase 3.
3. **If FAIL (Upscale detected):**
    * Execute `SoX` to generate a visual spectrogram PNG.
    * n8n moves the file to an `_Upscale_Review` folder on Unraid.
    * n8n sends a Discord webhook with the track name, the generated Spectrogram image, and a button to "Keep Anyway" or "Delete".

#### **Phase 3: LLM Metadata Enrichment (Windows API)**

For files that pass, n8n sends the messy metadata (from tags or `.info.json`) to your Windows PC via a POST request.

1. **The API Prompt:** Your FastAPI server queries Ollama (Llama 3.1) with strict system instructions:
    * *Standardize Roman Urdu* (e.g., Khatak -> Khattak).
    * *Split compound artists* (Extract featured artists).
    * *Format Output:* Require a strict JSON output using Pydantic validation.
2. **The Write:** A script running via `mutagen` writes the cleaned LLM JSON data directly into the FLAC/AAC file tags.

#### **Phase 4: Library Ingestion (Beets)**

Files are handed over to Beets on Unraid. The configuration is critical here:

1. Use Claude's recommended `quiet_fallback: asis` config. If Beets cannot find the track on MusicBrainz, it will still import the file using your LLM-cleaned tags rather than skipping it.
2. Set `data_source_mismatch_penalty: 0.0` for Discogs, as Discogs has a vastly superior database for Pakistani physical cassette/CD releases.
3. Use the `plexupdate` plugin to instantly trigger a Plexamp scan.

#### **Phase 5: The "Golden Loop" (MusicBrainz Contribution)**

This runs as a separate, asynchronous n8n workflow once a week. It scans your "Cleaned" library to give back to the community.

1. **Fully Automated Contributions (Headless):**
    * A script scans your library for files that have an ISRC tag or an existing MusicBrainz Recording ID.
    * It uses `pyacoustid` to generate an audio fingerprint.
    * It silently submits the fingerprint and ISRC to the AcoustID and MusicBrainz APIs.
2. **Semi-Automated Seed UI (Human in the Loop):**
    * For files that Beets imported "as-is" (meaning they don't exist on MusicBrainz), your Windows LLM generates MusicBrainz Seed parameters (ISO 639-3 language codes like `urd`, script codes, and formatted sort names).
    * Host a simple local webpage (via Flask/n8n) containing a "Pending Submissions" table.
    * Each row has a "Seed to MB" button. Clicking it opens your MacBook's browser to the MusicBrainz Release Editor, fully pre-filled. You visually verify the LLM's work, click "Submit," and save the community hours of manual data entry.

### Next Steps for You

1. **Setup the Windows API:** Install Python and Ollama on the Windows machine. Write a 30-line FastAPI script that accepts a JSON payload, wraps it in the Pakistani curation prompt, sends it to Ollama, and returns the JSON. Test this with `curl` from Proxmox.
2. **Spin up n8n:** Create the n8n Docker container on Proxmox/Unraid and build the first `ytmusicapi` polling node.

---

# Prompt

Okay thanks. So I want to make a few changes based on:

* I prefer n8n over huey because I already have that deployed fora different automation use case
* I tried out Yubal and it seems to work well enough for the YouTube playlist syncing aspect
* so now I have a couple of folders on my NAS that I need to organize and ingest: "/mnt/user/main/downloads/unseeded/music/tidal-dl", "/mnt/user/main/downloads/unseeded/music/yubal", "/mnt/user/main/downloads/unseeded/music/adhoc"
* what I want to do here is:
  * Yubal handles the continuous syncing and first pass downloading of files from my YouTube playlists
  * then I can bulk download into tidal-dl or have one-off files downloaded in the adhoc directory
  * I want the curation workflow to look through all these, do smart matching to figure out a superset list of all songs I have downloaded and maintain that as a user-friendly web UI backed by a clean database or something, update or clean metadata, then do symlinks into "/mnt/user/main/media/Music" for the best version of each song
  * the best version is the highest quality version. However I have found (through Fakin the Funk) that FLAC files on Tidal are sometimes just reencodes of lossy files, especially from indie artists. So I want this to be smarter than just based on stated bitrate or file extension

---

# Response

This is a highly sophisticated and excellent evolution of your architecture. Moving the YouTube syncing to Yubal and using n8n to orchestrate multiple ingress folders (`tidal-dl`, `yubal`, `adhoc`) creates a robust "Staging vs. Production" environment.

The biggest technical hurdles in your new requirements are **Entity Resolution** (knowing that a file in `yubal` is the exact same song as a file in `tidal-dl`) and **Automated Quality Analysis** (programmatically doing what "Fakin' The Funk" does).

Here is the concrete implementation plan to build this intelligent, n8n-orchestrated, superset curation engine.

---

### Part 1: Architecture & The "User-Friendly UI"

To build a clean database with a user-friendly UI *without* coding a full React/Vue app from scratch, you should use **PocketBase**.

PocketBase is a single-file backend that uses SQLite. It gives you a beautiful, modern Admin Web UI right out of the box, and a powerful REST API that n8n can interact with seamlessly.

**The PocketBase Database Schema:**
You will create two tables (Collections) to handle the 1-to-many relationship of "One Song" -> "Many Downloaded Files":

1. **Table: `Tracks` (The Superset Entity)**
    * `title` (String) - Cleaned by LLM
    * `artist` (String) - Cleaned by LLM
    * `acoustid` (String) - The audio fingerprint
    * `best_file_id` (Relation -> `Files`) - Points to the winning file
    * `mbid` (String) - MusicBrainz ID (if matched)
2. **Table: `Files` (The Raw Downloads)**
    * `track_id` (Relation -> `Tracks`)
    * `filepath` (String) - e.g., `/mnt/user/main/downloads/unseeded/music/tidal-dl/song.flac`
    * `source` (Select: `yubal`, `tidal`, `adhoc`)
    * `stated_quality` (String) - e.g., "FLAC", "320kbps", "128kbps"
    * `true_quality_score` (Number) - Generated by our audio analysis
    * `is_upscale` (Boolean) - True if Fake FLAC

---

### Part 2: Programmatic "Fakin' The Funk" (Audio Forensics)

You cannot rely on file extensions. A 128kbps YouTube rip stuffed into a FLAC container will still say "FLAC 1411kbps" in standard metadata.

To automate this in n8n, you need a deterministic command-line tool. **`flac-detective`** (a Python tool) or **`auCDtect`** are the industry standards.

You will create a Python script (`analyze_audio.py`) on your NAS (or in your n8n Docker container) that n8n calls via the "Execute Command" node.

**The Logic:**

1. **Frequency Roll-off:** Genuine CD-quality FLACs have frequencies reaching 22kHz. A 128kbps MP3/AAC hard-cuts at ~16kHz.
2. **The Command:** `flac-detective /path/to/song.flac --json`
3. **The Output:** It will return a JSON object classifying the file as `AUTHENTIC`, `WARNING`, `SUSPICIOUS`, or `FAKE_CERTAIN`.
4. **Scoring System (For n8n):**
    * `True FLAC (Authentic)` = 100 points
    * `AAC 256kbps (Yubal/YT Premium)` = 75 points
    * `MP3 320kbps (Authentic)` = 70 points
    * `Fake FLAC (Upscaled 128kbps)` = 30 points
    * `Opus/AAC 128kbps (Standard YT)` = 20 points

---

### Part 3: The n8n Orchestration Workflow

Here is how your n8n workflow operates, running on a trigger (e.g., every night at 2 AM, or via webhook when Yubal/Tidal-dl finishes a batch).

#### **Step 1: The Scanner (Ingestion)**

* **Node:** "Execute Command" or "Read Files"
* **Action:** Find all new audio files in `/mnt/user/main/downloads/unseeded/music/` (across all 3 subfolders) that do not yet exist in the PocketBase `Files` table.

#### **Step 2: Fingerprinting & Analysis (The Heavy Lifting)**

For each new file, n8n passes the filepath to a Python script that does three things and returns a single JSON object to n8n:

1. **Extracts Tags:** Uses `mutagen` to read existing Artist/Title.
2. **AcoustID:** Uses `fpcalc` (Chromaprint) to generate an audio fingerprint. This solves the "Smart Matching" problem. Even if Yubal names the file `Nusrat_Live.m4a` and Tidal names it `Nusrat Fateh Ali Khan - Track 1.flac`, their audio fingerprint is identical.
3. **Quality Check:** Runs `flac-detective` to determine the `true_quality_score`.

#### **Step 3: Entity Resolution (Smart Matching)**

* **Node:** "HTTP Request" (Querying PocketBase)
* **Action:** Search the `Tracks` table for an exact `acoustid` match.
  * *Fallback:* If `acoustid` fails, ask your local Ollama LLM to do a fuzzy comparison on the Artist/Title strings against your database to see if it's the same song.
* **Result:**
  * If it exists, attach this new file to the existing Track in PocketBase.
  * If it doesn't exist, create a new `Tracks` record, run the raw metadata through your local **LLM for cleaning** (fixing Pakistani transliteration, removing "(Official Video)"), save the clean tags, and then attach the file.

#### **Step 4: The "Best Version" Tournament**

* **Node:** "Code" (JavaScript/n8n internal logic)
* **Action:** Look at all files associated with a specific Track.
* **Logic:**
  * Compare `true_quality_score`.
  * If Tidal is `100` (True FLAC) and Yubal is `75` (AAC), Tidal wins.
  * If Tidal is `30` (Fake FLAC/Upscale) and Yubal is `75` (Native AAC 256kbps), **Yubal wins** (preventing spectral lies from polluting your main library).
* **Update DB:** Update the `best_file_id` in PocketBase to the winner.

#### **Step 5: Organization & Symlinking**

Once a winner is crowned (either it's a brand new track, or a new download beat an old download):

1. **Tag the Winner:** n8n tells a script to write the pristine, LLM-cleaned metadata into the winning file's ID3/Vorbis tags.
2. **Delete Old Symlink (If Applicable):** If an older version was previously the winner, remove its symlink from `/mnt/user/main/media/Music/...`
3. **Create New Symlink:**
    * Construct the target path: `/mnt/user/main/media/Music/{{Clean_Artist}}/{{Clean_Album}}/{{Clean_Title}}.ext`
    * **Node:** "Execute Command"
    * **Command:** `ln -sf "/mnt/user/main/downloads/unseeded/music/tidal-dl/winner.flac" "/mnt/user/main/media/Music/Artist/Album/Title.flac"`

---

### Part 4: How You Interact With This Setup

Because of how this is architected, your daily interaction becomes incredibly streamlined:

1. **Adding Music:** You just drop YouTube links into Yubal, or batch-download albums via `tidal-dl`. You dump one-off files into `adhoc`.
2. **The Magic:** n8n automatically detects them in the night, sees if it's a better version of something you already have, rejects fake FLACs, cleans the metadata using your local AI, and symlinks it to Plex.
3. **The UI (PocketBase):** You log into `http://your-nas-ip:8090/_/`. You see a beautiful, searchable table of your entire superset library.
    * You can see which files are currently the "Winner".
    * You can filter by `is_upscale = True` to see all the Fake FLACs Tidal tried to sneak by you.
    * If the AI hallucinated a tag, you can just edit the text field in the PocketBase UI. You can configure n8n to listen for "Updates" on the PocketBase table to instantly re-tag and re-symlink the file when you hit save.

### Implementation Checklist

1. **Spin up PocketBase:** Deploy the official Docker container on Unraid. Set up the two tables (`Tracks` and `Files`).
2. **Install Audio Tools:** Ensure the n8n container has access to `python3`, `fpcalc` (usually part of the `chromaprint` package), and `flac-detective` (`pip install flac-detective`).
3. **Build the n8n Core:** Start with just the ingestion and PocketBase updating. Get your `yubal` and `tidal` files showing up in your web UI first.
4. **Add the Quality Gate:** Integrate the `flac-detective` logic.
5. **Add Symlinking:** Build the final stage that writes the symlinks to your `/media/Music` folder so Plex/Plexamp can see them.
