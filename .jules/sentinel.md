# Sentinel's Journal

## 2026-02-25 - PocketBase Filter Injection
**Vulnerability:** PocketBase filter strings were manually constructed using naive `replace("'", "\\'")` escaping. This allowed injection if the input contained a backslash followed by a single quote (e.g., `foo\'bar`), which resulted in `foo\\'bar` (escaped backslash, unescaped quote).
**Learning:** PocketBase's filter syntax behaves like SQL strings where backslashes escape characters. Escaping only the quote character is insufficient; the escape character itself (backslash) must also be escaped first.
**Prevention:** Use a dedicated sanitization function (`sanitize_pb_filter`) that escapes backslashes before escaping quotes for all user-controlled input in filters.
