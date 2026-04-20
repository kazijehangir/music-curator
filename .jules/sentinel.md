## 2026-04-20 - Fix overly permissive CORS configuration
**Vulnerability:** FastAPI app configured with allow_origins=["*"] and allow_credentials=True, allowing any domain to perform cross-origin requests with credentials.
**Learning:** Default templates or quickstarts often leave CORS wide open. This exposes APIs to unauthorized cross-origin access and potential CSRF if session cookies are used.
**Prevention:** Always restrict CORS origins using a configurable allowlist via settings and set allow_credentials=False unless explicitly required.
