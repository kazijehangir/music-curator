## 2024-05-18 - N+1 query loops optimization
**Learning:** Optimizing sequential PocketBase DB queries (the N+1 problem) inside loops by fetching records in bulk using `get_full_list` and caching them in an in-memory dictionary is a highly performant pattern.
**Action:** Identify N+1 query patterns in loops and fetch records in bulk to optimize.
