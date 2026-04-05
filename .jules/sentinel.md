## 2026-04-05 - PocketBase Filter Injection via Unhandled Backslashes
**Vulnerability:** PocketBase filter parameters were sanitized using only single quote replacement, which fails if the input contains backslashes, allowing filter injection.
**Learning:** The Python PocketBase SDK lacks the parameterized query binding present in the JS SDK, making manual string interpolation necessary but prone to injection.
**Prevention:** Always use the custom sanitize_pb_filter utility from src.core.security to escape backslashes and single quotes safely.
