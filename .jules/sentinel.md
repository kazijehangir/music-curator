## 2024-05-28 - PocketBase Filter Injection via Unhandled Backslashes
**Vulnerability:** PocketBase Python SDK queries using f-strings and manual single-quote replacing are vulnerable to filter injection if the input contains a backslash before a quote.
**Learning:** The Python SDK lacks parameter binding, so replacing only single quotes allows an attacker to escape the inserted backslash, leaving the quote active.
**Prevention:** Always use the custom sanitize_pb_filter utility from src/core/security.py to escape backslashes first, then single quotes, before interpolation.
