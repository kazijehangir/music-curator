## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-06-12 - Parallelize Database Deletions
**Learning:** Sequential HTTP database operations in a loop (like deleting orphaned releases one by one) cause severe N+1 latency over the network. The PocketBase SDK's underlying httpx client is thread-safe.
**Action:** Wrap individual API calls in a worker function returning success/error tuples, and use `concurrent.futures.ThreadPoolExecutor` to execute them concurrently, avoiding race conditions on shared statistics.
