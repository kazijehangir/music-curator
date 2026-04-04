## 2024-05-24 - Restrict CORS Configuration
**Vulnerability:** Permissive CORS policy with wildcard allow_origins and allow_credentials set to True exposed the API to unauthorized cross-origin requests.
**Learning:** Default or overly broad CORS settings bypass browser security mechanisms and can leak sensitive data.
**Prevention:** Always use an explicit allowlist for cors_origins via configuration and set allow_credentials to False unless specifically required.