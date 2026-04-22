## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-04-22 - N+1 Query in Tagging Pipeline
**Learning:** Sequential queries in inner loops are a common performance anti-pattern. Fetching files for every release inside the tagging loop causes an N+1 query bottleneck.
**Action:** Use get_full_list to prefetch and dictionary-cache database records grouped by foreign key before entering the loop.
