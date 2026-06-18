## 2024-05-18 - Restrict over-permissive CORS wildcard
**Vulnerability:** The FastAPI application used `allow_origins=["*"]`, enabling any origin to access the API endpoints via CORS.
**Learning:** Overly permissive wildcard CORS configurations in sensitive APIs can lead to Cross-Site Request Forgery (CSRF) via cross-origin requests, as credentials and cross-site interaction become enabled.
**Prevention:** Hardcode or use configurable lists explicitly limiting `allow_origins` to known trusted endpoints (like `http://127.0.0.1:8090`). Ensure configurations parsing comma-separated strings or JSON arrays correctly map to Python lists without treating them as pure strings during iteration.
