## 2026-04-19 - Fix Overly permissive CORS configuration
**Vulnerability:** CORS was configured with allow_origins=["*"] and allow_credentials=True, allowing any origin to make cross-origin requests with credentials.
**Learning:** FastAPI's default example configuration for CORS is often insecurely copied into production without restricting origins.
**Prevention:** Always restrict allow_origins to a whitelist of known domains and set allow_credentials=False unless explicitly required for specific origins.
