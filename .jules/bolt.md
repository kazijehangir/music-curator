## 2026-04-14 - Bulk Prefetching for Analyze Service
**Learning:** The deduplication and primary election processes in run_analysis were performing expensive get_list and get_full_list queries inside a loop for each unanalyzed file, causing significant N+1 query bottlenecks. Caching these relations in-memory prevents severe performance degradation.
**Action:** Always prefetch database records into an in-memory dictionary before iterating over files for operations like fingerprint matching or fetching siblings, taking care to update the in-memory cache as new records are assigned.
