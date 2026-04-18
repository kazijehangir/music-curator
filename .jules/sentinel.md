## 2026-04-18 - Overly permissive CORS configuration
**Vulnerability:** CORS allow_origins was set to ["*"] with allow_credentials=True
**Learning:** This combination allows any site to make credentialed requests to the API
**Prevention:** Use an explicit allowlist in settings and set allow_credentials=False
