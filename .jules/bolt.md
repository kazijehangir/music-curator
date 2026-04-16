## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-04-16 - N+1 Query in Tagging Loop
**Learning:** The tagging service was making N+1 queries to fetch files per release.
**Action:** Use get_full_list to prefetch and group files into a dictionary before looping through releases.
