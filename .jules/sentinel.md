## 2024-05-15 - PocketBase Filter Injection
**Vulnerability:** Manual single quote escaping in PocketBase queries allows filter injection via unhandled backslashes.
**Learning:** String replacement like `.replace("'", "\'")` is insufficient because backslashes must be escaped first. The Python SDK lacks JS SDK's native parameter binding.
**Prevention:** Always use the custom `sanitize_pb_filter` utility to construct safe filter strings.
