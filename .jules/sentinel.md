## 2025-02-28 - [Overly Permissive CORS Policy]
**Vulnerability:** The FastAPI application used `allow_origins=["*"]`, allowing any website to make cross-origin requests to the API.
**Learning:** Permissive CORS configurations can lead to CSRF-like attacks and unauthorized data access if the API relies on ambient credentials or is exposed to the internet/internal networks.
**Prevention:** Explicitly define `cors_origins` in the application settings and configure the `CORSMiddleware` to strictly parse and allow only those specific origins.
