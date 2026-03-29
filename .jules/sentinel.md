## 2025-03-09 - PocketBase Filter Injection Fix
**Vulnerability:** Unsanitized backslashes and single quotes in file paths allowed filter injection in PocketBase queries, bypassing intended query logic.
**Learning:** Manual single quote escaping is insufficient; backslashes must be escaped first, then single quotes, because the Python SDK lacks the JS SDK's parameter binding.
**Prevention:** Always use the dedicated `sanitize_pb_filter` utility function to construct safe filter strings instead of ad-hoc string replacement.
