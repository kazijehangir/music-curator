## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-06-15 - Parallelize Sequential Deletes
**Learning:** Sequential deletions in an N+1 loop using `pb.collection(COLL_RELEASE).delete()` can be very slow when cleaning up large numbers of orphaned releases.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` to parallelize individual database delete operations. To avoid race conditions, structure worker threads to return their results and process them sequentially in the main thread using `executor.map`.
