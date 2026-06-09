## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-06-09 - PocketBase SDK Thread Safety
**Learning:** The PocketBase Python SDK uses `httpx.Client` internally which is thread-safe. This means we can safely parallelize individual database operations (like `.update()` or `.delete()`) to solve N+1 problems where batch endpoints aren't available.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` to execute multiple independent PocketBase updates or deletes concurrently. Iterate over `as_completed` results rather than mutating shared structures directly.
