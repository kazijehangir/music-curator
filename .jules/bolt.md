## 2024-05-18 - Optimized sequential DB queries with bulk fetching
**Learning:** In loops processing many files, making individual `get_list` queries to check if a file exists creates an N+1 query performance bottleneck.
**Action:** Use `get_full_list` to pre-fetch records and cache them in an in-memory dictionary. This avoids sequential database calls inside loops, significantly improving batch processing performance.
