## 2024-03-09 - [Restrict Insecure CORS Origins]
**Vulnerability:** Found `allow_origins=["*"]` configured in `src/api/main.py`. This overly permissive CORS policy allows any website to make unauthorized cross-origin API requests, which could expose internal data or trigger actions (like CSRF) if authentication is managed by cookies or if endpoints lack proper authorization checks.
**Learning:** The default `["*"]` policy was likely used for development convenience but was left in place in the main service initialization.
**Prevention:** Always use a configurable, restricted list of origins (e.g., via environment variable) to ensure that only expected frontends can interact with the API, even during development.
