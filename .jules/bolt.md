## 2024-05-24 - N+1 query problem in PocketBase file discovery
**Learning:** Optimizing sequential PocketBase DB queries inside loops by fetching records in bulk using get_full_list and caching them in an in-memory dictionary is a highly performant pattern.
**Action:** Pre-fetch existing records into a dictionary keyed by the lookup field before iterating over items.
