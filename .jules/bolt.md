## 2026-04-09 - Bulk prefetch for PocketBase
**Learning:** Sequential N+1 DB queries inside loops severely degrade performance, while bulk fetching with `get_full_list` and in-memory dict caching is a highly performant pattern. Silent failures during prefetch must be avoided.
**Action:** Always prefetch data outside loops using `get_full_list`, reduce payload with `query_params={"fields": "..."}`, and explicitly fail fast on exceptions.
