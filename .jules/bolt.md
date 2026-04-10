## 2026-04-10 - N+1 query loop for get_list vs get_full_list
**Learning:** Calling get_list individually inside a loop severely degrades performance. Using get_full_list to prefetch records into a dictionary eliminates the N+1 query bottleneck.
**Action:** Always bulk prefetch records into a memory dictionary using get_full_list before iterating over large loops.