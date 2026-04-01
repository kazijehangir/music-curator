## 2024-04-01 - Restrict Overly Permissive CORS Configuration
**Vulnerability:** The API used an overly permissive CORS configuration allowing any origin ('*') with credentials, exposing the API to Cross-Site Request Forgery (CSRF) and cross-origin data exposure.
**Learning:** FastAPI's default example allows '*' for origins, which was copied blindly without understanding the security implications for a production application that may process credentials.
**Prevention:** Always restrict allow_origins to an explicit allowlist of trusted domains and set allow_credentials=False unless explicitly required and securely configured.
