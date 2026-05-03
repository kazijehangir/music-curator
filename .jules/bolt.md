## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-05-03 - Concurrent PB Updates
**Learning:** Sequential `.update()` calls to Pocketbase in a loop represent a significant N+1 bottleneck, especially when the `httpx` and `api/batch` methods are unavailable.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` to parallelize individual `.update()` calls. Collect error results into a `stats["errors"]` array.
