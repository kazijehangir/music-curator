## 2026-04-24 - Fix overly permissive CORS
**Vulnerability:** CORS was configured with `allow_origins=["*"]` and `allow_credentials=True`.
**Learning:** This combination allows any site to perform authenticated cross-origin requests, leading to severe vulnerabilities.
**Prevention:** Always restrict `allow_origins` to known trusted domains and disable `allow_credentials` unless strictly necessary.
