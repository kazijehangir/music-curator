## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-05-08 - Restrict PocketBase get_full_list payloads using 'fields'
**Learning:** Using `get_full_list` without restricting fields can fetch significantly more data than required, causing slow performance and large memory overhead. PocketBase allows specifying exactly which fields to return using the `fields` query parameter.
**Action:** When calling `get_full_list()`, especially on large collections, always pass `query_params={"fields": ...}` restricted to just the schema attributes actually accessed in downstream code. Always include 'id' as it is required by the Python SDK for object mapping and updates.
