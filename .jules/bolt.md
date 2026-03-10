## 2024-03-24 - [Avoid N+1 get_list in os.walk]
**Learning:** Checking file existence one-by-one via `pb.collection('music_file').get_list(1, 1, ...)` inside an `os.walk` loop creates a massive N+1 network/DB bottleneck during discovery scans on large directories.
**Action:** When scanning directories or processing many files, pre-fetch all relevant records for that directory via `get_full_list` with a lightweight field projection (e.g., `query_params={"fields": "id,file_path,file_hash"}`). Build an in-memory dictionary keyed by `file_path` for O(1) existence checks.
