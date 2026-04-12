## 2026-04-12 - PocketBase Filter Injection
**Vulnerability:** Inadequate manual escaping of single quotes in pb filters.
**Learning:** The Python SDK requires backslashes to be escaped before single quotes to prevent trailing backslash injection.
**Prevention:** Use a dedicated sanitize_pb_filter utility.
