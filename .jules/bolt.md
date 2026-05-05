## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-05-05 - Unfiltered PocketBase API Calls
**Learning:** Fetching entire records using get_full_list without specifying fields can pull large, unnecessary payloads into memory.
**Action:** Use query_params={"fields": ...} to drastically reduce payload sizes and memory consumption during bulk operations. Include 'id' explicitly to ensure the PocketBase Python SDK works as intended.
