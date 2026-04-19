## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-04-19 - Prefetching in Tagging Loop
**Learning:** Sequential queries for related records within inner loops is a bottleneck.
**Action:** Prefetch related records using get_full_list and group them in an in-memory dictionary keyed by foreign key before the loop.
