## 2025-02-28 - PocketBase Filter Injection
**Vulnerability:** PocketBase filter queries were constructed using manual string replacement (`replace("'", "\\'")`), which is insufficient for security. Attackers could use backslashes to escape the closing quote (`hack\'` -> `hack\\'`), breaking out of the string literal.
**Learning:** Simple quote escaping is not enough when the escape character itself (backslash) is also a valid character in the input.
**Prevention:** Use a dedicated sanitization function that escapes backslashes *before* escaping quotes (`replace("\\", "\\\\").replace("'", "\\'")`).
