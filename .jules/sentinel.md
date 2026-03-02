## 2024-05-24 - PocketBase Filter Injection via File Paths
**Vulnerability:** The codebase was performing naive string replacement (`replace("'", "\\'")`) on user input (file paths) used directly in PocketBase filter strings.
**Learning:** If an attacker can control the input to contain both a backslash and a single quote (e.g., `foo\'bar`), naive replacement results in `foo\\'bar`. PocketBase interprets the double backslash as a literal backslash, leaving the single quote unescaped. This breaks the filter boundary and allows injection of arbitrary filter logic.
**Prevention:** Always use a dedicated sanitization function that escapes backslashes *before* escaping single quotes (`value.replace('\\', '\\\\').replace("'", "\\'")`).
