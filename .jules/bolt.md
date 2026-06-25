## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-06-25 - Parallelizing N+1 Database Deletions
**Learning:** Sequential calls to `pb.collection.delete()` in a loop represent an N+1 performance bottleneck during cleanup operations. The PocketBase Python SDK is thread-safe, so these can be safely parallelized.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` to parallelize individual deletions, but be careful to ensure shared state (like stats dictionaries) is updated safely in the main thread by iterating over `as_completed()` to avoid race conditions.
