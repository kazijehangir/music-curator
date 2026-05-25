## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-05-25 - Parallelizing PocketBase Updates
**Learning:** PocketBase Python SDK uses thread-safe httpx.Client, enabling safe parallelization of sequential updates.
**Action:** Use concurrent.futures.ThreadPoolExecutor to parallelize independent database update loops.
