# 📝 Music Curator Roadmap

This file tracks the implementation progress of the Music Curator pipeline based on `notes/final-implementation-plan.md`.

## Phase 1: PocketBase + Discovery (Days 1–6)

* [x] **Infrastructure**: Provision LXC, Unraid NAS mounts (`/mnt/user/main/downloads/unseeded/music/`, `/media/Music/`).
* [x] **API Scaffolding**: FastAPI structure, basic endpoints, pytest setup, systemd deployments.
* [x] **Deploy PocketBase**: Set up collections (`music_release`, `music_file`, `music_metadata_source`).
* [x] **Implement `/api/discover`**: Logic to walk ingest directories, hash files, extract metadata via `mutagen`, and insert into PocketBase.

## Phase 2: Fingerprinting + Quality + Dedup (Days 7–14)

* [x] **Fingerprinting**: Generate AcoustID via `pyacoustid` and store it.
* [x] **Quality Scoring**: FLAC Detective + librosa spectral rolloff.
* [x] **Deduplication**: Match fingerprints or fuzzy metadata, auto-group into `music_release`, and evaluate the `best_file`.
* [x] **Connect `/api/analyze`**.

## Phase 3: Symlinks + Plex (Days 15–19)

* [ ] **Symlink Manager**: Create paths in `/media/Music/` pointing to primary files.
* [ ] **Plex Integration**: Trigger Plex library scans.
* [ ] **Connect `/api/symlink`**.

## Phase 4: Metadata Intelligence (Days 20–26)

* [x] **Beets Integration**: Auto-match to MusicBrainz and store MBIDs.
* [x] **Mutagen Gap-Fill**: Read from sidecars (`.info.json`).
* [x] **LLM Normalization**: Send raw metadata to LMStudio for transliteration, parsing, genre inference.
* [x] **Connect `/api/tag`**.

## Phase 5: MusicBrainz Contribution (Days 27–32)

* [ ] **Batch Submit**: Submit ISRCs and fingerprints for matched recordings.
* [ ] **MBID Sync Tooling**: Run `beet mbsync` to pull new MBIDs.
* [ ] **Connect `/api/mb/batch-submit`** and `/api/mb/sync`.

## Phase 6: Polish (Days 33–35)

* [ ] **Realtime Hooks**: PocketBase editing triggers.
* [ ] **Health endpoint (`/api/health`)**.
