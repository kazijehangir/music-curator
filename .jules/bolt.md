## 2024-05-28 - Optimizing sequential PocketBase queries
**Learning:** Checking file existence sequentially in a loop against PocketBase causes an N+1 query problem, severely degrading performance when scanning large directories.
**Action:** Use `get_full_list` to fetch existing records in bulk before the loop and cache them in an in-memory dictionary.
