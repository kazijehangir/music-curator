## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-07-05 - Parallelize N+1 PocketBase Deletions
**Learning:** Sequential deletions of orphaned records cause massive N+1 overhead over the network API. The PocketBase SDK is thread-safe and can be effectively parallelized using `ThreadPoolExecutor`.
**Action:** Use `ThreadPoolExecutor` and iterate over `as_completed` to concurrently process independent database writes.
