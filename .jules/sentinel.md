## 2026-04-16 - Fix overly permissive CORS configuration
**Vulnerability:** The API used allow_origins=["*"] with allow_credentials=True, which is highly insecure.
**Learning:** This existed because CORS wasn't strictly configured for production, relying on wildcards.
**Prevention:** Always restrict CORS origins using a config variable and set allow_credentials=False unless necessary.
