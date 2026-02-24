## 2025-02-19 - Mocking PocketBase Queries and String Escaping
**Learning:**
1. When switching from `get_list` (single item) to `get_full_list` (batch), existing tests mocking `get_list` will fail silently or confusingly if `get_full_list` isn't also mocked. `get_full_list` returns a list of objects, not a list wrapped in a result object like `get_list` (which returns `Result(items=[...])`).
2. When constructing filter strings for PocketBase queries (or any SQL-like API), always escape user-provided inputs (like directory names) to prevent syntax errors with special characters like single quotes.

**Action:**
1. Always check existing tests for mocks of the API method being replaced, and ensure the new method is mocked to return the expected data structure (list of objects vs result object).
2. Always sanitize/escape inputs used in filter strings: `safe_val = val.replace("'", "\\'")`.
