## 2024-05-18 - [Optimization]
**Learning:** Checking for file existence one by one in pocketbase introduces the N+1 problem. Fetching them in bulk in Python is a much more performant pattern.
**Action:** When acting as "Bolt", implement bulk fetch optimizations instead of sequential DB queries.
