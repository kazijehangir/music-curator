## 2026-05-10 - Overly Permissive CORS Configuration
**Vulnerability:** The FastAPI application used `allow_origins=["*"]` combined with `allow_credentials=True`.
**Learning:** This combination allows any origin to send requests with credentials (like cookies or authorization headers) to the backend, which could expose sensitive data or actions to unauthorized domains via Cross-Site Request Forgery (CSRF) or malicious JavaScript.
**Prevention:** Instead of using wildcards for allowed origins when credentials are required, restrict the origins to an explicit allowlist (e.g., using a comma-separated configuration variable).
