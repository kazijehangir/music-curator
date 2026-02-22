import pytest
import json
import logging
import shutil
import httpx
from pathlib import Path

from src.core.schema import COLL_RELEASE, COLL_FILE, COLL_METADATA_SOURCE, MusicFile, Release, MetadataSource
from src.services.discover import run_discovery
from src.services.analyze import run_analysis
from src.services.tagging import run_tagging
from src.core.config import settings

logger = logging.getLogger(__name__)

# Load test cases
CONFIG_PATH = Path(__file__).parent / "data" / "testdata_config.json"
try:
    with open(CONFIG_PATH, "r") as f:
        TEST_CASES = json.load(f)
except Exception as e:
    logger.warning(f"Could not load test config: {e}")
    TEST_CASES = []


def test_schema_collections_exist(pocketbase_server):
    """
    Smoke test: all three application collections exist and are queryable via
    the SDK client. Fails fast if PB is unreachable or the fixture failed to
    seed the schema.
    """
    pb = pocketbase_server
    pb.collection(COLL_FILE).get_list(1, 1)
    pb.collection(COLL_RELEASE).get_list(1, 1)
    pb.collection(COLL_METADATA_SOURCE).get_list(1, 1)


def test_schema_fields_complete(pocketbase_server):
    """
    Verifies that all three collections were seeded with their full field
    definitions — not just empty shells.

    Covers three regression concerns in a single test:

    1. Field existence — catches PB API format regressions where custom fields
       are silently dropped (e.g. the 'schema' vs 'fields' key change in v0.22,
       or future format changes).

    2. Select field format — quality_verdict, mb_status, and source are select
       fields; if the flat format (values/maxSelect at top level) stops working,
       those fields will be missing or have no values.

    3. Relation field wiring — release, best_file, and file are relation fields
       that must point to the correct collection by PB-generated ID (not name).
       Verifies that init_schema's two-step create-then-PATCH approach correctly
       resolves and stores the real IDs.
    """
    token = pocketbase_server.auth_store.token
    headers = {"Authorization": token}

    def fetch_col(name: str) -> dict:
        resp = httpx.get(f"{settings.pocketbase_url}/api/collections/{name}", headers=headers)
        assert resp.status_code == 200, f"Could not fetch '{name}' collection: {resp.text}"
        return resp.json()

    file_col    = fetch_col(COLL_FILE)
    release_col = fetch_col(COLL_RELEASE)
    source_col  = fetch_col(COLL_METADATA_SOURCE)

    file_id    = file_col["id"]
    release_id = release_col["id"]

    def fields(col: dict) -> dict:
        """Return {field_name: field_definition} for a collection."""
        return {f["name"]: f for f in col.get("fields", [])}

    ff = fields(file_col)
    rf = fields(release_col)
    sf = fields(source_col)

    # Helper to get all fields from a schema class
    def get_fields(cls):
        return [v for k, v in cls.__dict__.items() if not k.startswith("_") and isinstance(v, str)]

    # ── music_file ────────────────────────────────────────────────────────────
    for name in get_fields(MusicFile):
        assert name in ff, f"music_file missing field '{name}'"

    assert ff.get(MusicFile.QUALITY_VERDICT, {}).get("type") == "select", \
        f"music_file.{MusicFile.QUALITY_VERDICT} should be a select field"
    assert "authentic" in ff.get(MusicFile.QUALITY_VERDICT, {}).get("values", []), \
        f"music_file.{MusicFile.QUALITY_VERDICT} missing 'authentic' value"

    assert ff.get(MusicFile.RELEASE, {}).get("type") == "relation", \
        f"music_file.{MusicFile.RELEASE} should be a relation field"
    assert ff.get(MusicFile.RELEASE, {}).get("collectionId") == release_id, \
        f"music_file.{MusicFile.RELEASE}.collectionId should be '{release_id}' (music_release), " \
        f"got '{ff.get(MusicFile.RELEASE, {}).get('collectionId')}'"

    # ── music_release ─────────────────────────────────────────────────────────
    for name in get_fields(Release):
        assert name in rf, f"music_release missing field '{name}'"

    assert rf.get(Release.MB_STATUS, {}).get("type") == "select", \
        f"music_release.{Release.MB_STATUS} should be a select field"
    assert "unknown" in rf.get(Release.MB_STATUS, {}).get("values", []), \
        f"music_release.{Release.MB_STATUS} missing 'unknown' value"

    assert rf.get(Release.BEST_FILE, {}).get("type") == "relation", \
        f"music_release.{Release.BEST_FILE} should be a relation field"
    assert rf.get(Release.BEST_FILE, {}).get("collectionId") == file_id, \
        f"music_release.{Release.BEST_FILE}.collectionId should be '{file_id}' (music_file), " \
        f"got '{rf.get(Release.BEST_FILE, {}).get('collectionId')}'"

    # ── music_metadata_source ─────────────────────────────────────────────────
    for name in get_fields(MetadataSource):
        assert name in sf, f"music_metadata_source missing field '{name}'"

    assert sf.get(MetadataSource.SOURCE, {}).get("type") == "select", \
        f"music_metadata_source.{MetadataSource.SOURCE} should be a select field"
    assert "musicbrainz" in sf.get(MetadataSource.SOURCE, {}).get("values", []), \
        f"music_metadata_source.{MetadataSource.SOURCE} missing 'musicbrainz' value"

    assert sf.get(MetadataSource.FILE, {}).get("type") == "relation", \
        f"music_metadata_source.{MetadataSource.FILE} should be a relation field"
    assert sf.get(MetadataSource.FILE, {}).get("collectionId") == file_id, \
        f"music_metadata_source.{MetadataSource.FILE}.collectionId should be '{file_id}' (music_file), " \
        f"got '{sf.get(MetadataSource.FILE, {}).get('collectionId')}'"


def test_discover_filter_by_path(pocketbase_server):
    """
    Verifies that filtering music_file by file_path works end-to-end.
    This isolates the exact query that discover.py makes before any pipeline
    logic runs, catching PB filter syntax regressions early.
    """
    pb = pocketbase_server
    test_path = "/tmp/test_filter_song.flac"

    rec = pb.collection(COLL_FILE).create({MusicFile.FILE_PATH: test_path, MusicFile.CODEC: "flac"})
    try:
        result = pb.collection(COLL_FILE).get_list(
            1, 1, {"filter": f"{MusicFile.FILE_PATH}='{test_path}'"}
        )
        assert result.total_items == 1, (
            f"Filter returned {result.total_items} items, expected 1. "
            "PB may not support single-quoted strings in filters."
        )
        assert result.items[0].id == rec.id
    finally:
        pb.collection(COLL_FILE).delete(rec.id)


@pytest.mark.parametrize("test_case", TEST_CASES)
def test_full_pipeline_e2e(test_env, test_case):
    """
    Data-driven end-to-end test that runs a real audio file through the full
    curation pipeline (discover → analyze → tag) and asserts the final
    metadata state in PocketBase.

    Test cases are defined in tests/integration/data/testdata_config.json.
    Each case specifies the audio file, an optional mock sidecar, and the
    expected field values on the resulting release record.
    """
    test_yubal, pb = test_env

    file_name   = test_case["test_file"]
    mock_sidecar = test_case.get("mock_sidecar", {})
    expected    = test_case.get("expectations", {})

    source_audio = Path(__file__).parent / "data" / file_name
    if not source_audio.exists():
        pytest.skip(f"Test audio file missing: {source_audio}. Skipping this test case.")

    # Place the audio file under Artist/Album directory structure in the ingest folder
    artist_dir = test_yubal / expected.get("expected_artist", "Unknown Artist")
    album_dir  = artist_dir / expected.get("expected_album", "Unknown Album")
    album_dir.mkdir(parents=True, exist_ok=True)

    dest_audio = album_dir / file_name
    shutil.copy(source_audio, dest_audio)
    logger.info(f"Copied test file to {dest_audio}")

    # Write sidecar info.json if the test case provides mock metadata
    if mock_sidecar:
        sidecar_path = dest_audio.with_name(f"{dest_audio.stem}.info.json")
        sidecar_path.write_text(json.dumps(mock_sidecar))
        logger.info(f"Wrote sidecar file {sidecar_path.name}")

    # ── 1. Discover ──────────────────────────────────────────────────────────
    logger.info("Starting PIPELINE STAGE: Discover")
    stats_discover = run_discovery(pb=pb, ingest_folders=["yubal"])
    logger.info(f"Discover stats: {stats_discover}")
    assert stats_discover["new_files"] == 1, "Discover should insert 1 new file"

    # ── 2. Analyze ───────────────────────────────────────────────────────────
    logger.info("Starting PIPELINE STAGE: Analyze")
    stats_analyze = run_analysis(pb=pb)
    logger.info(f"Analyze stats: {stats_analyze}")
    assert stats_analyze["analyzed"] == 1, "Analyze should process 1 file"
    assert stats_analyze["new_releases"] == 1, "Analyze should create 1 release grouping"

    # ── 3. Tag ───────────────────────────────────────────────────────────────
    logger.info("Starting PIPELINE STAGE: Tag")
    stats_tag = run_tagging(pb=pb)
    logger.info(f"Tag stats: {stats_tag}")
    assert stats_tag["tagged"] == 1, "Tagging should process 1 release"

    # ── 4. Verify final PocketBase state ──────────────────────────────────────
    logger.info("Verifying final PocketBase state")

    # Helper to clean/map expectation keys
    def get_expected(field_name: str) -> any:
        return expected.get(f"expected_{field_name}")

    # Helper to get all field names from a schema class
    def get_schema_fields(cls):
        return [v for k, v in cls.__dict__.items() if not k.startswith("_") and isinstance(v, str)]

    # Verify music_file record
    files = pb.collection(COLL_FILE).get_full_list()
    assert len(files) == 1, f"Expected 1 file record, got {len(files)}"
    file_record = files[0]

    for field in get_schema_fields(MusicFile):
        exp_val = get_expected(field)
        if exp_val is not None:
            actual_val = getattr(file_record, field, None)
            assert actual_val == exp_val, f"File field '{field}' mismatch: expected '{exp_val}', got '{actual_val}'"

    # Verify music_release record
    releases = pb.collection(COLL_RELEASE).get_full_list()
    assert len(releases) == 1, f"Expected 1 release record, got {len(releases)}"
    release_record = releases[0]

    for field in get_schema_fields(Release):
        exp_val = get_expected(field)
        if exp_val is not None:
            actual_val = getattr(release_record, field, None)
            assert actual_val == exp_val, f"Release field '{field}' mismatch: expected '{exp_val}', got '{actual_val}'"

    # Provenance: at least one metadata source record must exist after tagging
    sources = pb.collection(COLL_METADATA_SOURCE).get_full_list()
    assert len(sources) > 0, "No metadata sources were written during tagging"

    logger.info("E2E test passed.")
