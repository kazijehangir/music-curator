## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-06-05 - Parallelize PocketBase Deletes
**Learning:** PocketBase SDK uses `httpx.Client` which is thread-safe, allowing safe parallelization of network-bound operations like sequential deletes using `concurrent.futures.ThreadPoolExecutor`. Mutating shared structures like stats dicts should be done sequentially by yielding results from the worker to avoid race conditions.
**Action:** Use `concurrent.futures.ThreadPoolExecutor.map` combined with a worker function returning a tuple of success/error details to safely optimize `N+1` sequential database writes or deletes.
