## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-05-10 - Unfiltered get_full_list causes memory bloat
**Learning:** Fetching all columns via get_full_list() on large collections (like files or releases) parses massive JSON payloads, wasting memory when only a few fields are needed.
**Action:** Always provide the fields parameter in query_params when calling get_full_list, ensuring id is included for PocketBase SDK object mapping.
