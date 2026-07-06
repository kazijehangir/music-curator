## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2024-07-06 - Thread-safety in PocketBase SDK
**Learning:** The PocketBase Python SDK handles requests synchronously per instance by default. When wrapping PocketBase HTTP API operations (like `pb.collection().delete()`) in a ThreadPoolExecutor for concurrent execution, the SDK is thread-safe and allows N+1 operations to be parallelized successfully without internal lock contention.
**Action:** Always consider parallelizing sequential PocketBase operations where the latency per item is bound by network RTT, ensuring shared metrics state (e.g., `stats` objects) are mutated safely in the main thread using worker results.
