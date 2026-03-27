## 2025-02-28 - Filter Injection
**Vulnerability:** Manual string escaping in PocketBase filters (`file_path_str.replace("'", "\\'")`) is insufficient and leads to filter injection.
**Learning:** Backslashes are not escaped by default, meaning an attacker could craft a payload with backslashes to bypass the manual quote escaping logic in PocketBase queries built via Python string interpolation.
**Prevention:** Always use `sanitize_pb_filter` from `src.core.security` to securely construct PocketBase filter strings.
