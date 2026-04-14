## 2026-04-14 - Restrict Overly Permissive CORS Policy
**Vulnerability:** The FastAPI application used allow_origins=['*'] with allow_credentials=True, exposing the API to cross-origin attacks from any domain.
**Learning:** Defaulting to wildcard origins is a common pitfall during rapid development that leaves APIs vulnerable if not restricted before deployment.
**Prevention:** Always restrict allow_origins to a specific allowlist via application settings and explicitly set allow_credentials=False when not needed.
