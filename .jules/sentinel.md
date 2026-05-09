## 2026-05-09 - Overly Permissive CORS Configuration
**Vulnerability:** The API was configured with a wildcard origin allowing any site to perform authenticated cross-origin requests.
**Learning:** FastAPI middleware was configured with a wildcard origin and allowed credentials, which exposes the API to CSRF and cross-origin data theft.
**Prevention:** Always restrict CORS origins to an explicit allowlist defined in the application configuration when credentials are required.
