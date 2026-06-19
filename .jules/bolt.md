## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-06-19 - N+1 Query in API Deletions
**Learning:** Sequential PocketBase operations (like deletes) in a loop act as a severe bottleneck (N+1 problem over network I/O).
**Action:** Use concurrent.futures.ThreadPoolExecutor to parallelize independent database write operations to significantly reduce total execution time, while ensuring shared state (like stats) is updated sequentially in the main thread.
