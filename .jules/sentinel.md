## 2026-04-30 - Fix Overly Permissive CORS
**Vulnerability:** CORS configuration allowed any origin (`allow_origins=["*"]`) while also allowing credentials (`allow_credentials=True`).
**Learning:** This combination allows malicious sites to make authenticated requests on behalf of users, leading to CSRF-like attacks via fetch/XHR. FastAPI doesn't natively block this when configured explicitly, but some clients or reverse proxies will reject it.
**Prevention:** Always restrict `allow_origins` to an explicit allowlist of trusted domains when `allow_credentials=True` is required for the frontend.
