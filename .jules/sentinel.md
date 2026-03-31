## 2024-05-18 - PocketBase Filter Injection via String Replacement
**Vulnerability:** Constructing PocketBase queries using `str.replace("'", "\'")` to escape single quotes, which is vulnerable to backslash bypasses (e.g., `\'` -> `\` and an unescaped `'`).
**Learning:** Using simple string replacement is insufficient for securely escaping parameters in PocketBase Python SDK filter strings, as the Python SDK lacks the parameter binding (`pb.filter(query, {params})`) available in the JS SDK.
**Prevention:** Implement and use a robust `sanitize_pb_filter` utility function (e.g., in `src/core/security.py`) that strictly escapes both backslashes and single quotes.
