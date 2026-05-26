## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-05-26 - Thread Safety of PocketBase Python SDK
**Learning:** The PocketBase Python SDK utilizes `httpx.Client` internally, which is inherently thread-safe. This means we can safely parallelize slow, sequential N+1 `update()` loops bound by network latency using `concurrent.futures.ThreadPoolExecutor` without the need to rewrite the entire application to `async/await`.
**Action:** When encountering a large sequential N+1 loop for PocketBase operations (e.g. `.update()`), wrap the body in a worker function and parallelize it using `ThreadPoolExecutor`, returning explicit error strings or a sentinel (like "SKIP") to handle loop continuations accurately.
