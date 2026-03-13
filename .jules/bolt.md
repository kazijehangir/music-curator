# Bolt's Journal

## 2025-02-27 - PocketBase File Discovery N+1 Query Bottleneck
**Learning:** In the `run_discovery` process, checking if each file existed individually by calling `pb.collection('music_file').get_list(...)` inside an `os.walk` loop created an N+1 query problem. This caused massive performance degradation because it forced thousands of separate HTTP calls to PocketBase when scanning a large ingest directory.
**Action:** When performing existence checks or sync logic against PocketBase, always prefer batch-fetching the relevant scope (e.g. `get_full_list` filtered by `source_dir`) into an in-memory dictionary. Use standard dictionary lookups (`existing_files_dict.get(...)`) instead of repeated API calls within loops.