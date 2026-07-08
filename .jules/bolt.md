## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-07-08 - Parallelize Database N+1 Operations
**Learning:** Optimizing PocketBase database loops without a batch endpoint requires parallel execution via `ThreadPoolExecutor`. This is distinct from I/O operations over CIFS, which shouldn't be parallelized to avoid hangs.
**Action:** When a batch API isn't available, parallelize independent database updates/deletions via threads to mitigate network latency.
