## 2026-05-14 - Overly Permissive CORS Configuration

**Vulnerability:** The FastAPI application was configured to allow cross-origin requests from any origin while also allowing credentials.
**Learning:** Using a wildcard origin with credentials can expose the application to CSRF-like attacks from unauthorized domains.
**Prevention:** Always restrict CORS allowed origins to an explicit, configurable allowlist of trusted domains.
