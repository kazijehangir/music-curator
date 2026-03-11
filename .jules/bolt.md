## 2024-03-24 - N+1 Query Bottleneck in Discovery
**Learning:** The file discovery process originally queried PocketBase for every single file to check if it existed (`get_list` inside a loop), causing an N+1 query bottleneck. PocketBase supports `get_full_list` which can pre-fetch all records for a given `source_dir`.
**Action:** When iterating over a large number of files that need to be checked against a database, always prefer pre-fetching the relevant subset of records into an in-memory dictionary for O(1) lookups instead of querying the database inside the loop.
