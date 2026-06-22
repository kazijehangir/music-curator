## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-06-22 - Concurrent DB calls
**Learning:** Sequential N+1 delete calls to PocketBase are extremely slow over the network and can be optimized using `ThreadPoolExecutor`.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` when performing N+1 DB deletions or updates to hide network latency, while ensuring that the test suite accounts for non-deterministic execution order.
