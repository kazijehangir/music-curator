## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-04-28 - PocketBase Memory Footprint Optimization
**Learning:** Calling get_full_list() unconditionally fetches all fields of every record, which wastes memory and increases API payload size, risking Out-Of-Memory errors on large datasets.
**Action:** Always prefetch specific fields via query_params={"fields": f"id,{Model.FIELD}"} when retrieving large numbers of records. Ensure id is explicitly included for correct PocketBase Python SDK mapping.
