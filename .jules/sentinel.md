## 2026-03-17 - Fix Overly Permissive CORS Configuration
**Vulnerability:** The FastAPI application configured CORS middleware with `allow_origins=["*"]`, allowing any website to make cross-origin requests to the API.
**Learning:** Permissive CORS policies can expose the API to Cross-Site Request Forgery (CSRF) and unwanted access if authentication relies on ambient credentials (like cookies).
**Prevention:** Always restrict CORS `allow_origins` to known, trusted origins by configuring it via environment variables (e.g., `CORS_ORIGINS`).