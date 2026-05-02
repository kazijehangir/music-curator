## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-05-02 - PocketBase Bulk Query Payloads
**Learning:** Fetching full objects with get_full_list on large collections causes massive memory and payload overhead.
**Action:** Always restrict get_full_list with the fields parameter (e.g., query_params={"fields": "id,field1,field2"}) when only specific data is needed.
