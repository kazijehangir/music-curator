
## 2026-04-22 - Insecure CORS Configuration
**Vulnerability:** Overly permissive CORS settings (`allow_origins=["*"]` with `allow_credentials=True`) allowing potential CSRF.
**Learning:** Default wildcard settings in FastAPI's CORSMiddleware must be replaced with explicit allowlists, particularly when credentials might be used.
**Prevention:** Use `pydantic-settings` with a custom validator to securely parse comma-separated strings from environment variables into a list for `allow_origins`. Set `allow_credentials=False` unless explicitly needed.
