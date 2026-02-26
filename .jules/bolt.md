## 2024-05-23 - PocketBase N+1 Optimization in Batch Processing
**Learning:** In `run_analysis`, performing "Primary Election" (calculating the best file for a release) inside the file processing loop caused O(N^2) database operations when importing albums.
**Action:** Defer parent/aggregate updates to a separate loop after processing the batch. Use a `set` to track affected parent IDs and update them once. This reduced DB calls from 3N to N + M (where M is number of releases).
**CI Fix:** Ensure that deferred logic loops (like batch updates) have dedicated test cases covering their exception handling paths to maintain code coverage standards.
