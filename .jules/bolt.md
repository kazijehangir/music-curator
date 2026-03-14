## 2024-05-24 - Avoid N+1 Queries in File Discovery
**Learning:** Running database queries (like PocketBase `get_list`) inside an `os.walk` loop is a severe N+1 bottleneck when discovering files.
**Action:** Always pre-fetch existing records for the target directory in a single query (e.g., `get_full_list`) and filter them into an in-memory dictionary. Use the `fields` query parameter (like `fields='id,file_path,file_hash'`) to prevent excessive memory consumption when building the map.
