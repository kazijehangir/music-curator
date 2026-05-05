## 2026-05-05 - Reusable Security Pattern: Pydantic CORS Validation
**Vulnerability:** Overly permissive CORS configuration with wildcard origins and credentials allowed.
**Learning:** Using a comma-separated string for CORS origins in environments is common, but requires robust parsing to avoid misconfigurations.
**Prevention:** Use a Pydantic V2 `@field_validator` with `@classmethod` in the Settings class to automatically parse and sanitize comma-separated string inputs into an explicit list of allowed origins.
