## 2026-04-11 - Overly permissive CORS configuration
**Vulnerability:** The FastAPI application used allow_origins=["*"] with allow_credentials=True, allowing any website to make cross-origin requests.
**Learning:** The default setup prioritized ease of development over security, exposing the API to unauthorized cross-origin access.
**Prevention:** Use an explicit allowlist of origins from the configuration settings and disable allow_credentials unless explicitly required.
