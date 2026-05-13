## 2026-05-13 - Insecure CORS Configuration
**Vulnerability:** The FastAPI application used `allow_origins=["*"]` along with `allow_credentials=True`, which is overly permissive and potentially exposes the application to unauthorized cross-origin requests.
**Learning:** This existed likely for development convenience, but it violates the principle of least privilege and secure defaults, specifically making authenticated endpoints vulnerable.
**Prevention:** Always restrict CORS origins to an explicit allowlist in configuration, especially when credentials are allowed.
