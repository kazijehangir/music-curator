

## 2026-04-13 - N+1 Query Elimination in Discovery
**Learning:** Using get_list inside the file discovery loop causes severe N+1 query bottlenecks and slows down the scan.
**Action:** Use get_full_list outside the loop with specific query_params to fetch necessary fields, then use an in-memory dictionary for O(1) lookups.
