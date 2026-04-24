## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-04-24 - "Fetch All" Anti-Pattern in Symlink Service
**Learning:** Fetching an entire table unconditionally (`get_full_list()` without filters) causes OOM errors and wastes memory when only a subset is needed.
**Action:** Query dependent files first, extract unique foreign keys, and batch-fetch parent records in chunks (e.g. 50 items) using dynamic `||` filters. Specify only needed fields.
