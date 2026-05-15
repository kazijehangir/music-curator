## 2026-05-15 - Overly Permissive CORS Configuration
**Vulnerability:** CORS was globally allowed while also allowing credentials.
**Learning:** FastAPI's default quickstart often uses permissive origins which is dangerous when combined with credentials, exposing the API to cross-origin attacks.
**Prevention:** Always restrict allow_origins to an explicit allowlist defined in configuration, and parse it properly during application startup.
