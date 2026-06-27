## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-06-27 - Parallelize PocketBase Deletions
**Learning:** PocketBase SDK is thread-safe and can handle concurrent database calls over ThreadPoolExecutor. This is useful for optimizing N+1 database operations when the /api/batch endpoint is unavailable.
**Action:** When sequential PocketBase operations become a bottleneck, use ThreadPoolExecutor with `as_completed` to parallelize them, ensuring that shared structures are updated sequentially in the main thread to avoid race conditions.
