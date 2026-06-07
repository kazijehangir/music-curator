## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-06-07 - Parallelize PocketBase Deletes
**Learning:** PocketBase Python SDK is thread-safe, making it safe to run parallel delete operations.
**Action:** Use concurrent.futures.ThreadPoolExecutor for N+1 PocketBase update or delete API calls, but ensure you do not mutate shared dictionaries within the worker threads.
