## 2024-05-24 - Restrict CORS Origins
**Vulnerability:** Overly permissive CORS configuration allowing all origins and credentials.
**Learning:** FastAPI's CORSMiddleware must be configured with specific origins when credentials are allowed to prevent cross-origin exploits.
**Prevention:** Use a configuration variable to enforce an allowlist of trusted origins and disable allow_credentials if not strictly needed.
