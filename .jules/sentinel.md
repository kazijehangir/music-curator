## 2025-02-23 - CORS Misconfiguration
**Vulnerability:** Permissive CORS origins with credentials enabled.
**Learning:** Using '*' for origins alongside allow_credentials=True exposes authenticated data to arbitrary origins.
**Prevention:** Always restrict CORS origins using a strict configuration allowlist and disable credentials if not needed.
