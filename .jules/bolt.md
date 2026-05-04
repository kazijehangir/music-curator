## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-05-04 - Optimize PocketBase Bulk Fetches Payload Size
**Learning:** Fetching all fields in `get_full_list` can cause large payload sizes and OOM risks, especially for tables with large string fields like AcoustID footprints.
**Action:** Always specify the minimum required fields including `id` using `query_params={"fields": ...}`.
