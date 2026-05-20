## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-05-20 - PocketBase Payload Optimization
**Learning:** Calling `get_full_list()` without restricting fields returns massive objects when only a few fields are needed, causing unnecessary JSON serialization overhead and latency.
**Action:** Always supply the `fields` query parameter, ensuring `id` is included, whenever fetching records that are only used for specific property lookups.
