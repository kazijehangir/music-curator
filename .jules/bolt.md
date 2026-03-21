## 2024-03-24 - Pre-fetch files to avoid N+1 queries during discovery
**Learning:** Optimizing sequential PocketBase DB queries (the N+1 problem) inside loops by fetching records in bulk using `get_full_list` and caching them in an in-memory dictionary is a highly performant pattern.
**Action:** Always pre-fetch existing records and populate a hash map before iterating through large datasets like files on disk, to prevent sequential network and database lookups.
