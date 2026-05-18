## 2026-05-18 - Fix Overly Permissive CORS Configuration
**Vulnerability:** The FastAPI application was configured with an overly permissive CORS policy, allowing all origins (`allow_origins=["*"]`) while also allowing credentials (`allow_credentials=True`).
**Learning:** This is a security risk as it could allow any malicious website to make cross-origin requests on behalf of a user and read sensitive responses. This is explicitly discouraged. It existed because it's an easy way to get around CORS issues during development, but wasn't restricted for production.
**Prevention:** Always restrict CORS origins to an explicit allowlist in production environments, particularly when `allow_credentials=True` is set. Configure allowed origins via environment variables.
