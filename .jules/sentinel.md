## 2026-04-07 - Overly permissive CORS configuration
**Vulnerability:** CORSMiddleware configured with allow_origins=['*'] and allow_credentials=True
**Learning:** Using wildcard origins with credentials is insecure; restrict via an allowlist using pydantic-settings with a field_validator to parse comma-separated strings safely.
**Prevention:** Always explicitly define allow_origins and set allow_credentials=False unless strictly necessary.
