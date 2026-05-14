## 2024-05-24 - Overly Permissive CORS Policy
**Vulnerability:** The FastAPI server used `allow_origins=["*"]` in the `CORSMiddleware` configuration in `src/api/main.py`. This allows any website to make cross-origin requests, including potentially malicious sites.
**Learning:** This occurred because a permissive default was used during development and wasn't restricted for production.
**Prevention:** Always restrict CORS origins to explicitly allowed domains via an environment variable or configuration file. Never commit `allow_origins=["*"]` into the codebase.