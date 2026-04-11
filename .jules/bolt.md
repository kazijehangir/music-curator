## 2026-04-11 - Bulk Prefetch Exception Handling
**Learning:** Pre-fetching records avoids N+1 queries, but exceptions must be explicitly handled to prevent massive duplicate inserts if the DB is unreachable.
**Action:** Always use explicit try-except blocks and fail fast during bulk prefetch.
