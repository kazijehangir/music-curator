## 2024-04-03 - N+1 Query in discover.py
**Learning:** Sequential PocketBase API queries inside file discovery loops create an N+1 performance bottleneck.
**Action:** Use get_full_list with query_params fields restriction and cache results in a dictionary before looping.
