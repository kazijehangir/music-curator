## 2024-03-20 - Initialization
**Learning:** Initializing journal to comply with rules.
**Action:** Ready to document critical findings.

## 2024-03-20 - N+1 Query in file discovery
**Learning:** Checking for existing files one by one via `get_list(1, 1, ...)` inside an `os.walk` loop creates a massive N+1 bottleneck during discovery. Fetching all existing file paths at once using `get_full_list` and storing them in an in-memory dictionary avoids this.
**Action:** Replace `get_list` inside loops with a bulk prefetch using `get_full_list` mapped into a dictionary.

## 2024-03-20 - N+1 Query in file analysis
**Learning:** In `analyze.py`, checking for duplicate fingerprints one by one using `get_list(1, 2, ...)` inside a loop over unanalyzed records also creates an N+1 query issue, just like in discovery.
**Action:** The same bulk prefetching technique using `get_full_list` and mapping fingerprints to existing release IDs should be used to eliminate the N+1.
