## 2024-05-24 - PocketBase N+1 Queries
**Learning:** Checking for file existence one-by-one with `get_list` in a loop causes a massive N+1 bottleneck when scanning directories.
**Action:** Use `get_full_list` before the loop to pre-fetch records into an in-memory dictionary. Use `query_params` (e.g., `{'fields': 'id,file_path,file_hash'}`) to fetch only necessary fields and save memory.
