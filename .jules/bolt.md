## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-07-02 - N+1 Network I/O in Cleanup Task
**Learning:** Sequential PocketBase delete requests in a background maintenance task (`cleanup_orphaned_releases`) suffer from significant N+1 network latency, making it unnecessarily slow for large orphan sets. The PocketBase SDK is thread-safe and can handle concurrent API calls efficiently.
**Action:** Always wrap loops that dispatch independent HTTP/Database I/O requests inside `concurrent.futures.ThreadPoolExecutor`. Ensure that shared mutable state (like `stats` dicts) is only updated sequentially on the main thread (e.g., using `as_completed`) to prevent race conditions.
