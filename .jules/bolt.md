## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-07-01 - Parallelizing N+1 Database Writes
**Learning:** PocketBase lacks an `/api/batch` endpoint, causing sequential looping for bulk operations (like deletes) to become a severe I/O bottleneck.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` to parallelize individual API calls instead of sequential loops, ensuring thread-safe collection of error stats by resolving futures in the main thread.
