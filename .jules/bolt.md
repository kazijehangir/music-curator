## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-05-14 - PocketBase N+1 Query Fix
**Learning:** Calling `get_full_list()` on large collections without filters or field limits fetches the entire table into memory, leading to high latency and potential OOM errors (the "Fetch All" anti-pattern).
**Action:** When prefetching relational data (like releases for files), fetch the main entities first, extract the needed IDs, and fetch only those IDs in chunks (e.g. 50-100) using `fields` restriction and multiple `||` conditions in the `filter` parameter.
