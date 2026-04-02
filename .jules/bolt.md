## 2024-05-24 - Bulk Prefetching Optimization
**Learning:** Optimizing sequential PocketBase queries inside loops by bulk fetching with get_full_list and caching in an in-memory dictionary is a highly performant pattern.
**Action:** Replace N+1 get_list queries with get_full_list bulk fetching and O(1) dictionary lookups.
