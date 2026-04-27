## 2026-04-27 - Fix Overly Permissive CORS
**Vulnerability:** CORS configured with allow_origins=["*"] and allow_credentials=True, allowing unauthorized cross-origin requests.
**Learning:** Using allow_origins=["*"] with allow_credentials=True is insecure and typically prohibited by modern browser specifications. Explicit allowlists should always be used.
**Prevention:** Always use explicit lists of allowed origins for CORS, especially when credentials are permitted.
