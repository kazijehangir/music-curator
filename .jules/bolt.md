## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-06-10 - PocketBase Python SDK Thread Safety
**Learning:** The PocketBase Python SDK utilizes a thread-safe `httpx.Client` internally. This allows PocketBase API calls (such as `.delete()` or `.update()`) to be safely parallelized using `concurrent.futures.ThreadPoolExecutor` without encountering race conditions in the HTTP client.
**Action:** Use `ThreadPoolExecutor` to parallelize N+1 PocketBase database operations when the `/api/batch` endpoint is unavailable, ensuring to handle shared state (like error collections) sequentially in the main thread by iterating over `as_completed()`.
