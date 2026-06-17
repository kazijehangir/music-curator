## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-06-17 - Non-Deterministic Executions in Concurrent Collections
**Learning:** When refactoring sequential operations to use concurrent execution (e.g., `concurrent.futures.ThreadPoolExecutor`), the order of execution is non-deterministic. Tests that verify the contents of resulting collections (like arrays of collected errors) against exact indices will fail intermittently if not updated.
**Action:** Update associated tests to handle non-deterministic execution order, such as by using `or` conditions or verifying against a set of expected strings instead of checking exact indices.
