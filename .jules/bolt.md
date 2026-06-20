## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-06-20 - Parallelize PocketBase API Deletions
**Learning:** Sequential calls to external APIs in loops (e.g. deleting orphaned PocketBase records) create severe N+1 bottlenecks. Modifying shared dictionaries (like `stats`) inside threads is unsafe.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` to parallelize independent external API calls. Instead of returning dictionaries, have worker threads return status tuples and process them sequentially via `as_completed()` in the main thread to safely update shared state.
