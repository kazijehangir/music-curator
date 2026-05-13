## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-05-13 - Optimize get_full_list queries with fields parameter
**Learning:** Using get_full_list() in PocketBase without specifying fields fetches large, unnecessary data like raw_meta and acoustid_fp, leading to excessive memory use and larger payloads.
**Action:** Always include a "fields" query parameter with get_full_list() to retrieve only the required attributes, making sure to include 'id' as the SDK relies on it.
