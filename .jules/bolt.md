## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-05-23 - Parallelize I/O bound loop in reanalyze_quality
**Learning:** Performing multiple synchronous operations (file parsing, subprocess calls, database updates) sequentially inside a loop creates severe N+1 blocking anti-patterns.
**Action:** Use concurrent.futures.ThreadPoolExecutor to parallelize individual tasks in the loop. Replace 'continue' statements with specific sentinel return values like 'SKIP' and properly aggregate errors and successes.
