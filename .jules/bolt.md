## 2026-03-31 - Fix N+1 Query in run_discovery
**Learning:** Optimizing sequential PocketBase DB queries (the N+1 problem) inside loops by fetching records in bulk using get_full_list and caching them in an in-memory dictionary is a highly performant pattern.
**Action:** Use get_full_list to prefetch existing records into memory before processing items in a loop instead of making individual get_list API calls.
