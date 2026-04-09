## 2026-04-09 - PocketBase Filter Injection via Unescaped Backslashes
**Vulnerability:** PocketBase filter strings constructed with manual single quote escaping are vulnerable to injection via trailing backslashes.
**Learning:** The Python PocketBase SDK lacks the parameter binding present in the JS SDK, making manual string concatenation dangerous if backslashes aren't escaped first.
**Prevention:** Always use a dedicated sanitization utility that safely escapes backslashes before single quotes for all PocketBase queries in Python.