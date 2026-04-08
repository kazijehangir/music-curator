## 2026-04-08 - Fix N+1 queries in run_discovery
**Learning:** Sequential PocketBase DB queries inside loops cause severe performance bottlenecks.
**Action:** Optimize by fetching records in bulk using get_full_list and caching them in an in-memory dictionary.
