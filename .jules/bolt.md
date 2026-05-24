## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-05-24 - Parallelize Database Updates
**Learning:** Sequential calls to update remote databases (like PocketBase .update) inside tight loops cause unnecessary scaling delays.
**Action:** Parallelize independent .update calls using concurrent.futures.ThreadPoolExecutor while collecting stats through mapped return values and sentinels.
