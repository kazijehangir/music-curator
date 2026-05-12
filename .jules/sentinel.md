## 2026-05-12 - Fix Overly Permissive CORS Configuration
**Vulnerability:** The FastAPI CORS middleware in `src/api/main.py` was configured with `allow_origins=["*"]` while simultaneously setting `allow_credentials=True`.
**Learning:** This is a classic security misconfiguration that allows any origin to make authenticated cross-origin requests, potentially exposing sensitive data.
**Prevention:** Restrict `allow_origins` to an explicit allowlist (e.g., using a configuration variable like `cors_allowed_origins`) and avoid using wildcards with `allow_credentials=True`.
