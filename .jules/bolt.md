## 2025-03-01 - Optimizing N+1 Database Queries in File Discovery
**Learning:** Checking for the existence of records individually inside a loop using PocketBase `get_list` leads to severe N+1 performance bottlenecks when scanning a large number of files.
**Action:** Always pre-fetch existing records in bulk using `get_full_list` with minimal required fields (e.g., `id`, `file_path`, `file_hash`) before the loop, and construct an in-memory dictionary for O(1) lookups to avoid redundant database calls.
