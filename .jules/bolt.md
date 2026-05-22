## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-05-22 - Avoid 'Fetch All' Anti-Pattern for Memory Efficiency
**Learning:** Calling get_full_list() without filters to build a lookup dictionary for foreign keys (the 'Fetch All' anti-pattern) causes major memory bottlenecks as databases grow.
**Action:** Prefetch relevant records by chunking target IDs and building a dynamic filter string using || conditions to resolve N+1 querying issues without fetching the entire table.
