## 2026-04-13 - Overly Permissive CORS Configuration
**Vulnerability:** Overly permissive CORS allowed all origins with credentials, presenting a potential CSRF risk.
**Learning:** Using allow_origins=['*'] with allow_credentials=True in FastAPI allows any external site to read authenticated API responses.
**Prevention:** Use an explicit allowlist and set allow_credentials=False.
