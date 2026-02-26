## 2026-02-26 - PocketBase Filter Injection via Backslashes
**Vulnerability:** PocketBase filter strings were manually constructed by only escaping single quotes (`value.replace("'", "\\'")`). This allowed injection if the input contained a backslash followed by a single quote (e.g., `foo\'bar`), as the backslash would escape the escape character, leaving the single quote active.
**Learning:** Manual filter construction is error-prone. Standard string replacement is insufficient when the target system (PocketBase) uses backslash as an escape character.
**Prevention:** Use `src.core.security.sanitize_pb_filter` for all dynamic values in PocketBase filters. Always escape backslashes *before* escaping single quotes.
