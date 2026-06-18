## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-04-06 - PocketBase SDK Thread Safety
**Learning:** The PocketBase Python SDK is thread-safe and can be used within a ThreadPoolExecutor for concurrent requests without issues.
**Action:** Use ThreadPoolExecutor to parallelize independent N+1 database API calls where batch endpoints aren't available.
