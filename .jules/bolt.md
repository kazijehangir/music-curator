## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-05-12 - Optimize Bulk Reads in Background Services
**Learning:** Calling get_full_list() without specifying fields pulls the entire record payload into memory, causing out-of-memory errors on large collections.
**Action:** Always use the 'fields' parameter in get_full_list() queries, restricting the payload to exactly what the logic needs, and explicitly include 'id' as the PocketBase SDK requires it.
