import pytest
import signal
import subprocess
import time
import httpx
import os
import shutil
from pathlib import Path
from tempfile import mkdtemp

from src.core.config import settings
from src.core.schema import COLL_RELEASE, COLL_FILE, COLL_METADATA_SOURCE
from pocketbase import PocketBase

PB_BIN = (Path(__file__).parent / "test_bin" / "pocketbase").resolve()
PB_TEST_PORT = 8099


def _kill_stale_pb(port: int):
    """Kill any leftover PocketBase processes on the test port."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True
        )
        for pid in result.stdout.strip().split():
            if pid:
                os.kill(int(pid), signal.SIGKILL)
        if result.stdout.strip():
            time.sleep(0.5)
    except Exception:
        pass


def _create_superuser(pb_bin: str, pb_data_dir: str, email: str, password: str):
    """Create superuser via CLI before the server starts (PB v0.23+)."""
    result = subprocess.run(
        [pb_bin, "superuser", "upsert", email, password, "--dir", pb_data_dir],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to create superuser: {result.stderr}\n{result.stdout}"
        )


def _get_superuser_token(pb_url: str, email: str, password: str) -> str:
    """Authenticate as superuser via the PB v0.25 _superusers collection."""
    resp = httpx.post(
        f"{pb_url}/api/collections/_superusers/auth-with-password",
        json={"identity": email, "password": password}
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Superuser auth failed ({resp.status_code}): {resp.text}")
    return resp.json()["token"]


def init_schema(pb_url: str, token: str):
    """
    Create application collections in four explicit steps:

    Step 1 — DB/users: handled by the caller before init_schema is invoked.
    Step 2 — Create bare collection shells (no fields, no relations).
    Step 3 — Fetch the PB-generated ID for each collection.
    Step 4 — PATCH each collection with its full field list, using real
             collection IDs (not names) for every relation field. This is
             the only reliable way to create relations in PB v0.23+.

    Circular dependency (music_file ↔ music_release) is resolved naturally:
    both shells exist before either is patched with relation fields.
    """
    headers = {"Authorization": token}

    open_rules = {"listRule": "", "viewRule": "", "createRule": "", "updateRule": "", "deleteRule": ""}

    # ── Step 2: Create bare collection shells ─────────────────────────────────
    def create_bare(name: str) -> str:
        """POST a bare collection and return its PB-generated ID."""
        payload = {"name": name, "type": "base", **open_rules}
        res = httpx.post(f"{pb_url}/api/collections", json=payload, headers=headers)
        if res.status_code == 400 and "validation_collection_name_exists" in res.text:
            # Already exists from a previous test run — fetch its real ID.
            res2 = httpx.get(f"{pb_url}/api/collections/{name}", headers=headers)
            if not res2.is_success:
                raise RuntimeError(
                    f"Collection '{name}' exists but could not be fetched: "
                    f"{res2.status_code} {res2.text}"
                )
            return res2.json()["id"]
        if not res.is_success:
            raise RuntimeError(
                f"Failed to create collection '{name}': {res.status_code} {res.text}"
            )
        return res.json()["id"]

    # ── Step 3: Fetch actual PB-generated IDs ─────────────────────────────────
    file_id    = create_bare(COLL_FILE)
    release_id = create_bare(COLL_RELEASE)
    source_id  = create_bare(COLL_METADATA_SOURCE)

    # ── Step 4: Seed fields using real IDs for relation collectionId ──────────
    def patch_fields(col_id: str, col_name: str, fields: list):
        res = httpx.patch(
            f"{pb_url}/api/collections/{col_id}",
            json={"fields": fields},
            headers=headers,
        )
        if not res.is_success:
            raise RuntimeError(
                f"Failed to seed fields for '{col_name}': {res.status_code} {res.text}"
            )

    # music_file — relation to music_release (release grouping)
    patch_fields(file_id, COLL_FILE, [
        {"name": "release",                        "type": "relation",
         "collectionId": release_id, "maxSelect": 1, "cascadeDelete": False},
        {"name": "source_dir",                     "type": "text"},
        {"name": "file_path",                      "type": "text"},
        {"name": "file_hash",                      "type": "text"},
        {"name": "acoustid_fp",                    "type": "text"},
        {"name": "raw_title__raw_artist__raw_album", "type": "text"},
        {"name": "codec",                          "type": "text"},
        {"name": "sample_rate",                    "type": "number"},
        {"name": "bit_depth",                      "type": "number"},
        {"name": "bitrate",                        "type": "number"},
        {"name": "duration_seconds",               "type": "number"},
        {"name": "quality_score",                  "type": "number"},
        {"name": "quality_verdict",                "type": "select",
         "values": ["authentic", "warning", "suspicious", "fake", "lossy"], "maxSelect": 1},
        {"name": "spectral_ceiling",               "type": "number"},
        {"name": "is_primary",                     "type": "bool"},
        {"name": "symlink_path",                   "type": "text"},
    ])

    # music_release — relation to music_file via best_file
    patch_fields(release_id, COLL_RELEASE, [
        {"name": "title",           "type": "text"},
        {"name": "artist",          "type": "text"},
        {"name": "album",           "type": "text"},
        {"name": "genre",           "type": "text"},
        {"name": "language",        "type": "text"},
        {"name": "mb_recording_id", "type": "text"},
        {"name": "mb_release_id",   "type": "text"},
        {"name": "mb_status",       "type": "select",
         "values": ["unknown", "matched", "pending", "submitted", "synced"], "maxSelect": 1},
        {"name": "isrc",            "type": "text"},
        {"name": "best_file",       "type": "relation",
         "collectionId": file_id, "maxSelect": 1, "cascadeDelete": False},
        {"name": "file_count",      "type": "number"},
        {"name": "needs_review",    "type": "bool"},
    ])

    # music_metadata_source — relation to music_file
    patch_fields(source_id, COLL_METADATA_SOURCE, [
        {"name": "file",       "type": "relation",
         "collectionId": file_id, "maxSelect": 1, "cascadeDelete": False},
        {"name": "source",     "type": "select",
         "values": ["file_tags", "info_json", "musicbrainz", "discogs", "llm", "manual"], "maxSelect": 1},
        {"name": "field_name", "type": "text"},
        {"name": "value",      "type": "text"},
        {"name": "confidence", "type": "number"},
    ])


@pytest.fixture(scope="session")
def pocketbase_server():
    """Spins up a hermetic PocketBase server and initializes the schema."""
    if not PB_BIN.exists():
        pytest.fail(f"PocketBase binary not found at {PB_BIN}.")

    pb_data_dir = mkdtemp(prefix="pb_test_data_")
    pb_url = f"http://127.0.0.1:{PB_TEST_PORT}"
    admin_email = "test@musiccurator.local"
    admin_pass = "test_password12345"

    # 1. Kill any stale PB from a previous crashed test run
    _kill_stale_pb(PB_TEST_PORT)

    # 2. Create superuser via CLI BEFORE starting the server
    _create_superuser(str(PB_BIN), pb_data_dir, admin_email, admin_pass)

    # 3. Start PB server (cwd=pb_data_dir avoids picking up repo's pb_migrations/)
    pb_log = open("/tmp/pb_test.log", "w")
    process = subprocess.Popen(
        [str(PB_BIN), "serve", "--dir", pb_data_dir,
         "--http", f"127.0.0.1:{PB_TEST_PORT}"],
        stdout=pb_log, stderr=pb_log,
        cwd=pb_data_dir,
    )

    # 4. Wait for PB to become responsive
    server_ready = False
    for _ in range(50):
        try:
            if httpx.get(f"{pb_url}/api/health").status_code == 200:
                server_ready = True
                break
        except Exception:
            pass
        time.sleep(0.1)
    if not server_ready:
        process.kill()
        pytest.fail("PocketBase failed to start. Check /tmp/pb_test.log")

    # 5. Authenticate as superuser (PB v0.25 _superusers collection)
    token = _get_superuser_token(pb_url, admin_email, admin_pass)

    # 6. Override app settings for the test session
    settings.pocketbase_url = pb_url
    settings.pocketbase_admin_email = admin_email
    settings.pocketbase_admin_password = admin_pass

    # 7. Create application collections
    init_schema(pb_url, token)

    # 8. Create SDK client authenticated via _superusers collection
    pb = PocketBase(pb_url)
    pb.collection("_superusers").auth_with_password(admin_email, admin_pass)

    yield pb

    # Shutdown
    process.terminate()
    process.wait()
    pb_log.close()
    shutil.rmtree(pb_data_dir, ignore_errors=True)

@pytest.fixture(scope="function")
def test_env(pocketbase_server, tmp_path):
    """
    Function-scoped fixture to provide isolated test directories
    and clean PB collections before each test.
    """
    pb = pocketbase_server

    # Clean the collections
    for collection_name in [COLL_METADATA_SOURCE, COLL_FILE, COLL_RELEASE]:
        try:
            records = pb.collection(collection_name).get_full_list()
            for r in records:
                try:
                    pb.collection(collection_name).delete(r.id)
                except:
                    pass
        except Exception:
            pass

    # Create test directories
    test_ingest = tmp_path / "ingest"
    test_yubal = test_ingest / "yubal"
    test_yubal.mkdir(parents=True)
    test_media = tmp_path / "media"
    test_media.mkdir(parents=True)

    orig_ingest = settings.ingest_dirs
    orig_media = settings.media_library_path

    # Override internal paths
    settings.ingest_dirs = "yubal"
    settings.ingest_base_path = str(test_ingest)
    settings.media_library_path = str(test_media)

    yield test_yubal, pb

    settings.ingest_dirs = orig_ingest
    settings.media_library_path = orig_media
    settings.ingest_base_path = "tests" # Dummy reset
