## 2024-05-24 - PocketBase Filter Injection
**Vulnerability:** Manual single quote replacement (`.replace("'", "\\'")`) used for PocketBase queries is insecure and allows filter injection.
**Learning:** Backslashes are not escaped by single quote replacement, allowing an attacker to escape the substituted backslash and inject arbitrary filter syntax. The Python SDK lacks the parameter binding (`pb.filter()`) present in the JS SDK.
**Prevention:** Always use a dedicated escaping function (like `sanitize_pb_filter`) that strictly escapes backslashes first, then single quotes, before inserting values into a PocketBase filter string.
