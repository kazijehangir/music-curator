## 2025-02-21 - PocketBase N+1 Queries
**Learning:** Fetching records individually inside a loop via `get_list` in PocketBase creates an N+1 query bottleneck, especially when iterating over files like in `run_discovery`.
**Action:** Pre-fetch all relevant records using `get_full_list` with `query_params={'fields': 'id,file_path,file_hash'}` to reduce memory usage, build an in-memory dictionary mapping `file_path` to the record, and use dictionary lookups instead of individual database calls inside the loop.
