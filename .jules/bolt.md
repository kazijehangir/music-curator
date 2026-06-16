## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-06-16 - Parallelize PocketBase Deletes
**Learning:** PocketBase SDK is thread-safe. Sequential API deletes form an N+1 anti-pattern.
**Action:** Use concurrent.futures.ThreadPoolExecutor to parallelize individual update/delete API calls to PocketBase.
