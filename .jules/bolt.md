## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-06-30 - Parallelize Database Deletes
**Learning:** When optimizing PocketBase N+1 database operations via concurrency (e.g., ThreadPoolExecutor), avoid mutating shared data structures directly in worker threads.
**Action:** Return outcomes (e.g., success boolean and error message) from workers and update shared structures sequentially in the main thread using as_completed.
