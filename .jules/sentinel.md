## 2026-05-02 - Overly Permissive CORS and Pydantic V2 Validation
**Vulnerability:** FastAPI app allowed credentials with wildcard origins (`allow_origins=["*"]`, `allow_credentials=True`), a critical misconfiguration that allows any origin to make authenticated requests.
**Learning:** Pydantic V2 requires `@classmethod` alongside `@field_validator` in `BaseSettings` to correctly parse comma-separated env vars for explicit allowlists without crashing.
**Prevention:** Always restrict CORS to explicit allowlists using `cors_origins: Union[str, List[str]]` and avoid using `["*"]` when `allow_credentials=True` is set.
