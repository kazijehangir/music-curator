## 2026-04-07 - Bulk Pre-fetching PocketBase Records
**Learning:** Sequential PocketBase queries (N+1 problem) inside loops significantly degrade performance, especially over network boundaries.
**Action:** Optimize by fetching all necessary records in bulk before the loop using `get_full_list` and caching them in an in-memory dictionary keyed by their identifiers (e.g., file paths) for O(1) lookups during iteration.
