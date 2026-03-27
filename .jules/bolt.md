## 2024-05-24 - PocketBase N+1 query problem during discovery loops
**Learning:** Making individual PocketBase `get_list` calls for every file during directory scanning is incredibly slow and results in an N+1 query problem, especially when parsing large music libraries over network mounts.
**Action:** When performing bulk operations or scans against PocketBase records, always fetch all records upfront using `get_full_list`, store them in a python dictionary hashed by their unique identifier (like file path), and perform lookups against the dictionary instead of querying the API in the loop.
