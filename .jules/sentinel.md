## 2026-04-29 - Overly Permissive CORS Configuration
**Vulnerability:** CORS configuration allowed all origins (`*`) while also allowing credentials (`allow_credentials=True`).
**Learning:** Using a wildcard for allowed origins when credentials are allowed is a security risk and can expose the API to unauthorized cross-origin requests.
**Prevention:** Define explicitly allowed origins via configuration and restrict them, especially when `allow_credentials` is true.
