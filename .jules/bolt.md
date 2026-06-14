## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-06-14 - Concurrent mock execution
**Learning:** `unittest.mock.MagicMock` with a list `side_effect` is thread-safe for simple iterations in concurrent code.
**Action:** Use it safely in tests without introducing manual locking in `ThreadPoolExecutor` context.
