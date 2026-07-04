## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-07-04 - ThreadPoolExecutor mocking and DB vs I/O parallelism
**Learning:** When using `concurrent.futures.ThreadPoolExecutor` to speed up database N+1 operations, mocked methods in tests (e.g., `side_effect = [...]`) will pop elements in a non-deterministic order. Also, database API concurrency is safe, but avoid parallelizing CIFS file system I/O due to severe performance regressions or D-state hangs.
**Action:** Always use a callable `side_effect` function (e.g., `lambda rid: ...`) when mocking methods that will be executed concurrently, and explicitly restrict parallelism to HTTP/Database calls rather than disk operations in this architecture.
