## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-06-06 - N+1 Network Operations in Cleanup Loop
**Learning:** Sequential network operations (like deleting items) in loops create severe N+1 latency bottlenecks, especially since the PocketBase Python SDK uses thread-safe `httpx.Client`.
**Action:** When performing independent bulk updates or deletes against PocketBase without a batch endpoint, use `concurrent.futures.ThreadPoolExecutor` with a worker function returning a success/error tuple. This safely speeds up operations while avoiding shared state mutation race conditions.
