## 2026-05-16 - Restrict CORS Allowed Origins
**Vulnerability:** Overly permissive CORS configuration (`allow_origins=["*"]`) combined with `allow_credentials=True` allowed any origin to make authenticated requests.
**Learning:** Hardcoding wildcard CORS settings during development can easily leak into production. Using an explicitly defined allowlist tied to the configuration is necessary.
**Prevention:** Always define `cors_allowed_origins` in configuration and parse it during middleware initialization instead of using wildcards.
