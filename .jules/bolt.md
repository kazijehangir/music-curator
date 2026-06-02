## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-06-02 - PocketBase SDK Thread Safety
**Learning:** The PocketBase Python SDK uses httpx.Client internally, making it thread-safe. This allows PocketBase API calls to be safely parallelized using `concurrent.futures.ThreadPoolExecutor`.
**Action:** Parallelize independent database operations instead of executing them sequentially.
