## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-07-07 - Parallelize PocketBase Deletes
**Learning:** PocketBase lacks a native batch API, causing N+1 bottlenecks on mass deletes. Because the Python SDK is thread-safe, `concurrent.futures.ThreadPoolExecutor` can safely parallelize network I/O to improve throughput.
**Action:** Use `ThreadPoolExecutor` with `as_completed` for bulk updates/deletes in PocketBase to mitigate network roundtrip delays.
