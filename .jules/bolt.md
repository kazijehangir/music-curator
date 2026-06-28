## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-06-28 - Parallelize Sequential Deletes
**Learning:** Sequential database operations (like deletions) in a loop cause an N+1 bottleneck, slowing down the process unnecessarily when network latency is involved.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` to safely parallelize independent PocketBase API network operations (which is thread-safe), being careful to return results from workers and aggregate them sequentially in the main thread to avoid race conditions.
