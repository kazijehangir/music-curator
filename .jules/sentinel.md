## 2024-05-15 - [Overly Permissive CORS]
**Vulnerability:** Found `allow_origins=["*"]` in `src/api/main.py`.
**Learning:** Hardcoded permissive CORS origin is a security risk allowing cross-origin requests from any domain.
**Prevention:** Use an environment variable to define allowed CORS origins dynamically.
