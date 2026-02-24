# Sentinel Journal

## 2025-02-19 - PocketBase Filter Injection
**Vulnerability:** Found a PocketBase filter injection vulnerability in `src/services/discover.py`. The code was manually constructing a filter string using an f-string: `f"file_path='{safe_path_str}'"`. It only escaped single quotes (`'`) but not backslashes (`\`). This allowed an attacker to input a filename like `foo\'bar.mp3`, which would be escaped to `foo\\'bar.mp3`. In the filter string `file_path='foo\\'bar.mp3'`, the `\\` is interpreted as a literal backslash, leaving the `'` unescaped, which closes the string early and allows injecting arbitrary filter logic (e.g., ` || id='...'`).
**Learning:** Manual string concatenation for query filters is dangerous even with partial escaping. PocketBase filter syntax treats `\` as an escape character, so it must be escaped as `\\` when intended as a literal.
**Prevention:** Always escape backslashes before escaping quotes when sanitizing strings for PocketBase filters. Ideally, use a query builder that handles parameter binding if available (though PocketBase Python SDK uses string filters).
