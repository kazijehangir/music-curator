## 2026-05-03 - Fix overly permissive CORS settings
**Vulnerability:** The FastAPI application used `allow_origins=["*"]` with `allow_credentials=True`, which is an overly permissive CORS configuration.
**Learning:** This existed because the application might be accessed from various internal networks, but using `*` with credentials allows any website to make authenticated requests.
**Prevention:** Always restrict `allow_origins` to an explicit allowlist of trusted domains, especially when `allow_credentials=True` is set. Use a configuration setting that can be overridden via environment variables if needed.
