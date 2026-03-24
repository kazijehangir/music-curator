## 2024-05-24 - Bulk Prefetching for N+1 Queries
**Learning:** Sequential PocketBase API calls (`get_list`) inside file scanning loops create severe N+1 query bottlenecks, especially over network boundaries.
**Action:** Optimize sequential PocketBase DB queries inside loops by fetching records in bulk using `get_full_list` and caching them in an in-memory dictionary before iterating. Let the query fail fast rather than silencing exceptions to prevent massive duplicate inserts.
