## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-06-29 - PocketBase Python SDK is Thread-Safe for Concurrency
**Learning:** The PocketBase Python SDK safely supports concurrent requests from background threads. A common sequential loop over HTTP operations (e.g., deleting orphaned records one-by-one) causes severe N+1 latency. We can safely parallelize these operations using Python's `concurrent.futures.ThreadPoolExecutor`, turning O(N) network operations into O(N/M).
**Action:** When working on PocketBase operations that iterate over multiple records for isolated updates or deletes, use `ThreadPoolExecutor` to batch network requests concurrently. Always mock the SDK appropriately in tests using callable `side_effect`s instead of lists, because thread execution order is non-deterministic.
