## 2026-05-06 - Overly Permissive CORS Configuration
**Vulnerability:** The FastAPI application was configured with an overly permissive CORS setup that allowed any origin while simultaneously allowing credentials.
**Learning:** This combination exposes the application to CSRF and data exfiltration risks because it allows any origin to send requests with authentication credentials.
**Prevention:** Always explicitly define allowed origins in a configuration allowlist when credentials are required, instead of relying on wildcards.
