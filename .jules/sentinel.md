## 2026-05-07 - Fix Overly Permissive CORS Configuration
**Vulnerability:** The application used an overly permissive CORS configuration that allowed all origins.
**Learning:** This existed because it's a common default during development, but it leaves the application vulnerable to unauthorized cross-origin requests.
**Prevention:** Always restrict CORS allowed origins to an explicit allowlist of trusted domains, especially when credentials support is enabled.
