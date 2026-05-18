## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-05-18 - Parallelizing API Updates
**Learning:** In bulk maintenance scripts (like reanalyze_quality), iterating sequentially over records and calling update() causes massive IO bottlenecks over network shares.
**Action:** Use concurrent.futures.ThreadPoolExecutor to parallelize individual update() calls, as the PocketBase Python SDK uses a thread-safe httpx.Client.
