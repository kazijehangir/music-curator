## 2026-04-01 - N+1 Query Optimization
**Learning:** Silent failures in bulk prefetching (like falling back to an empty dictionary) can lead to massive duplicate record inserts if the database is unreachable
**Action:** Explicitly handle exceptions during bulk prefetching and fail fast to prevent data corruption
