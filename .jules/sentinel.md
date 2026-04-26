## 2026-04-26 - Fix overly permissive CORS configuration
**Vulnerability:** The FastAPI app was configured with `allow_origins=["*"]` combined with `allow_credentials=True`, which is an overly permissive CORS configuration.
**Learning:** This combination allows any site to make cross-origin requests with credentials, potentially exposing sensitive data.
**Prevention:** Always restrict CORS origins to known, trusted domains using an allowlist configured via environment variables.
