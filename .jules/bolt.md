## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-05-07 - PocketBase SDK Memory Bloat
**Learning:** Unfiltered get_full_list queries in PocketBase fetch all fields, causing severe memory bloat and large network payloads. The SDK maps all returned attributes.
**Action:** Always prefetch using the fields parameter in query_params (e.g. query_params={"fields": "id,title"}). The 'id' field is strictly required by the Python SDK for object mapping.
