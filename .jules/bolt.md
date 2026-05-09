## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-05-09 - Optimize Bulk Fetches with Fields Parameter
**Learning:** Using get_full_list without restricting fields can cause high memory usage and large payload sizes, which becomes a bottleneck.
**Action:** Always use the 'fields' parameter in PocketBase queries to fetch only the data that is actually needed, significantly reducing data transferred over the network.
