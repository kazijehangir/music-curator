## 2026-04-06 - Manual Filter Sanitization Vulnerability
**Vulnerability:** PocketBase filter strings were manually sanitized using string replace for single quotes, missing backslash escaping which leads to injection vulnerabilities.
**Learning:** The Python PocketBase SDK lacks automatic parameter binding, making string formatting dangerous without comprehensive escaping.
**Prevention:** Always use the dedicated src.core.security.sanitize_pb_filter function for all PocketBase filter parameters.
