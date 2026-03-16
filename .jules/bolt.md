## 2025-02-28 - N+1 query problem with PocketBase `get_list` in loops

**Learning:** Using `get_list` inside nested iterations (e.g. `os.walk` or similar loops over large sets) to check for existence of records individually causes severe N+1 query bottlenecks in PocketBase.
**Action:** Always prefer pre-fetching records efficiently with `get_full_list` grouped by a parent condition (e.g. `source_dir`), and performing existence checks and updates via in-memory dictionary lookups.
