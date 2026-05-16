## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-05-16 - PocketBase Database Fetch Optimization
**Learning:** Avoid micro-optimizing PocketBase database queries by restricting payload sizes using the `fields` parameter unless completely necessary and meticulously verified. The minor performance gains over heavy I/O operations (like metadata extraction or hashing) do not justify the high risk of severe `AttributeError` regressions if downstream logic silently accesses un-fetched fields.
**Action:** Instead of field restriction micro-optimizations, prioritize fixing structural bottlenecks like N+1 queries.
