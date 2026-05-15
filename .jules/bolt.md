## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-05-15 - Avoid Fetch All Anti-Pattern in Symlink
**Learning:** Fetching all records without filters causes unnecessary memory overhead and risks OOM errors.
**Action:** Use chunked get_full_list() calls and restricted field payloads.
