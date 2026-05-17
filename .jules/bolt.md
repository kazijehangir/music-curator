## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-05-17 - Prefetch files via ID chunking to fix N+1
**Learning:** Fetching related records per loop item causes N+1 problems, but blind get_full_list() causes OOM errors on large datasets.
**Action:** Prefetch related records by chunking target IDs into dynamic filter strings to limit queries safely.
