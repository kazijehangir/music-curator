# Bolt's Journal

## 2024-05-18 - [Optimized PocketBase Discovery with O(1) Dictionary Lookups]
**Learning:** Calling `get_list` in an iteration creates a severe N+1 query bottleneck. PocketBase `get_full_list` takes a `query_params` dict containing `"fields"` which allows minimizing the memory overhead when fetching massive collections.
**Action:** Always pre-fetch existing records into memory via `get_full_list(query_params={"fields": "id,file_path,file_hash"})` as a fast local dictionary before scanning directories or bulk verifying.
