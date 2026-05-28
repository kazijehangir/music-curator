## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-05-28 - Parallelize PocketBase Updates
**Learning:** PocketBase Python SDK uses httpx.Client, making it thread-safe for parallel updates like batching N+1 queries using ThreadPoolExecutor.
**Action:** Use concurrent.futures.ThreadPoolExecutor for N+1 HTTP database operations when bulk/batch endpoints are unavailable.
