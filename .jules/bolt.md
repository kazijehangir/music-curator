## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-04-06 - Parallelized PocketBase API Delete Calls
**Learning:** Sequential HTTP API calls in a loop (N+1 latency) severely bottleneck database operations when cleaning up orphaned records, even when the SDK wrapper is thread-safe.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` to execute individual PocketBase `.delete()` or `.update()` calls in parallel, returning execution status rather than mutating shared dictionaries inside worker threads.
