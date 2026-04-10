## 2026-04-10 - Filter Injection via Incomplete Escaping
**Vulnerability:** Single quote escaping without escaping backslashes allows PocketBase filter injection.
**Learning:** The Python SDK lacks parameter binding for filters, requiring full string sanitization.
**Prevention:** Always escape backslashes and single quotes using sanitize_pb_filter.
