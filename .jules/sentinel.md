## 2025-04-25 - Overly Permissive CORS Configuration
**Vulnerability:** The FastAPI application uses `CORSMiddleware` with `allow_origins=["*"]` and `allow_credentials=True`.
**Learning:** This is an insecure combination that violates the CORS specification and exposes the API to unauthorized cross-origin requests.
**Prevention:** Always restrict `allow_origins` to specific trusted domains or use a configurable allowlist via environment variables.
