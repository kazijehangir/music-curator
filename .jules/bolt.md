## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-04-27 - Optimize bulk fetches in PocketBase
**Learning:** Using get_full_list without the fields parameter fetches unnecessary payload, increasing data transfer and memory usage.
**Action:** Pre-calculate and specify the required fields (including 'id') in the query_params for bulk list fetches to minimize payload.
