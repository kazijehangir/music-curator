
## 2026-05-17 - Fix Overly Permissive CORS
**Vulnerability:** CORS was configured with allow_origins=["*"] and allow_credentials=True, allowing any origin to access the API with credentials.
**Learning:** FastAPI allows "*" with credentials in some old versions but it is a major security risk (and fails in newer versions). It must be restricted to known origins.
**Prevention:** Always define an explicit allowlist for CORS in config.py and never use "*" when credentials are required.
