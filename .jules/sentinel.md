## 2024-05-24 - Overly Permissive CORS Policy
**Vulnerability:** Found `allow_origins=["*"]` in FastAPI CORS configuration, which could allow any origin to make requests with credentials.
**Learning:** Hardcoded, overly permissive CORS settings bypass important browser security mechanisms and can lead to CSRF or sensitive data exposure if credentials are allowed.
**Prevention:** Always parse `cors_origins` from environment configurations or use specific, restrictive default values instead of wildcard allowlists for origins.