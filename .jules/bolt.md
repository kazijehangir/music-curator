## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-06-13 - Parallelize PocketBase Deletions
**Learning:** The PocketBase Python SDK utilizes `httpx.Client` internally, which is thread-safe, making it perfectly safe to parallelize `.delete()` calls with `concurrent.futures.ThreadPoolExecutor` without custom locking.
**Action:** Default to parallelizing I/O-heavy loops of PocketBase database operations where order is irrelevant.
