## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-05-19 - Optimize symlink release fetching N+1 problem
**Learning:** PocketBase's get_full_list() without filters can fetch huge amounts of data and cause OOMs or slow down operations significantly if only a subset of data is needed. The 'Fetch All' anti-pattern.
**Action:** Replaced unconditional fetch of all releases with a chunked fetch only for releases that are referenced by primary files, building dynamic filter strings to avoid SQLite's limits.
