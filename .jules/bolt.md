## 2024-05-23 - PocketBase N+1 Query Trap
**Learning:** PocketBase's `get_list` inside loops for file checks creates a severe N+1 bottleneck. Each file check becomes a network roundtrip.
**Action:** Always pre-fetch existing records using `get_full_list(query_params={'fields': 'id,file_path,file_hash'})` and use an in-memory dictionary lookup for existence checks.
