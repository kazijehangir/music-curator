## 2024-04-04 - Bulk Prefetch N+1 Queries
**Learning:** Sequential PocketBase queries in loops cause severe N+1 bottlenecks.
**Action:** Bulk prefetch records using get_full_list with specific fields and cache them in an in-memory dictionary, ensuring exceptions fail fast.
