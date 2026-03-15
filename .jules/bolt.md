## 2024-05-18 - N+1 Query Optimization in PocketBase
**Learning:** Performing `get_list` inside an `os.walk` loop creates an N+1 query bottleneck that scales linearly with the number of files, significantly slowing down discovery on large directories.
**Action:** Pre-fetch all records for the target scope (e.g., a specific `source_dir`) using `get_full_list` before iterating, and use an in-memory dictionary lookup for O(1) existence checks.
