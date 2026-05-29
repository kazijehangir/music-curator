## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-05-29 - Parallelizing PocketBase SDK calls
**Learning:** The Python PocketBase SDK utilizes an underlying httpx.Client that is thread-safe. This allows I/O blocking API operations like updates/deletes inside loops (N+1 queries) to be safely parallelized using `concurrent.futures.ThreadPoolExecutor` without raising concurrency exceptions.
**Action:** When encountering N+1 sequential loop operations calling the PocketBase SDK, convert them to concurrent executor maps handling results via a sentinel or dictionary return.
