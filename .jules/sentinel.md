## 2026-04-17 - Overly Permissive CORS Configuration
**Vulnerability:** The FastAPI application used allow_origins=['*'] with allow_credentials=True, exposing the API to unauthorized cross-origin requests.
**Learning:** Default permissive CORS configs in FastAPI combined with credentials allow unauthorized cross-origin data access.
**Prevention:** Restrict CORS origins via config and disable credentials if not strictly necessary.
