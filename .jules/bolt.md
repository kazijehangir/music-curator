## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-05-21 - Parallelizing PocketBase Updates
**Learning:** The Python `httpx.Client` underlying the PocketBase SDK is thread-safe. This allows expensive sequential file I/O operations paired with remote database updates to be safely parallelized using `concurrent.futures.ThreadPoolExecutor`.
**Action:** Use a `ThreadPoolExecutor` to parallelize sequential PocketBase iterations that combine blocking I/O (like audio analysis) with `.update()` calls, avoiding complex chunking when bulk endpoints are unavailable.
