## 2026-04-08 - Fix Filter Injection Vulnerability
**Vulnerability:** Manual single-quote escaping in PocketBase filters.
**Learning:** Escaping fails to handle trailing backslashes.
**Prevention:** Always use sanitize_pb_filter.
