## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-04-06 - Sequential PocketBase Updates
**Learning:** Making sequential PocketBase API updates in a loop is slow due to network latency, but httpx is thread-safe and allows parallelization.
**Action:** Use concurrent.futures.ThreadPoolExecutor.map to parallelize independent database updates to significantly reduce execution time.
