## YYYY-MM-DD - [Title]
**Vulnerability:** [What you found]
**Learning:** [Why it existed]
**Prevention:** [How to avoid next time]
## 2026-05-20 - Fix permissive CORS with credentials
**Vulnerability:** Overly permissive CORS with credentials enabled.
**Learning:** This leaves the API vulnerable to Cross-Site Request Forgery (CSRF) and malicious cross-origin data reads if a user has active session credentials.
**Prevention:** Always configure an explicit `cors_allowed_origins` allowlist parsed from settings instead of relying on wildcard origins when credentials are required.
