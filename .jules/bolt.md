## 2024-05-18 - N+1 Query in Discovery Service
**Learning:** Checking for file existence one-by-one inside `os.walk` using `get_list` in PocketBase creates an N+1 query problem that scales terribly with large folders.
**Action:** Pre-fetch existing records into an in-memory dictionary grouped by file path, and check the dictionary instead of querying PocketBase per file.
