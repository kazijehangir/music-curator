## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-04-26 - PocketBase Payload Optimization
**Learning:** Fetching entire database records when only a few fields are needed causes significant JSON payload bloat and memory overhead in Python.
**Action:** Always use the `fields` parameter in PocketBase `get_full_list()` queries to only return required attributes.
