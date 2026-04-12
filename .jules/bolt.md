## 2026-04-12 - Bulk Prefetch in Discovery
**Learning:** run_discovery loops over files and performs an individual PocketBase query per file (N+1), which scales poorly for large ingest folders.
**Action:** Always prefetch existing records via get_full_list and cache them in a dictionary keyed by file path before iterating over disk files.
