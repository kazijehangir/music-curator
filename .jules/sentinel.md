## 2026-04-23 - Fix Overly Permissive CORS
**Vulnerability:** FastAPI app configured with `allow_origins=["*"]` and `allow_credentials=True`.
**Learning:** Starlette `CORSMiddleware` rejects requests from disallowed origins with a 400 Bad Request status code ('Disallowed CORS origin') when `allow_origins` is explicitly set, rather than returning a 200 OK with missing access-control headers.
**Prevention:** Avoid wildcard origins in production configurations, and define explicit allowlists via environment variables using custom Pydantic validators for lists.
