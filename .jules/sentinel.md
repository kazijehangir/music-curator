## 2024-05-24 - Overly Permissive CORS Configuration
**Vulnerability:** The FastAPI application used `allow_origins=["*"]` in `CORSMiddleware`, which allows any website to make cross-origin requests to the API.
**Learning:** This existed because it was likely easier to configure during initial development but was never secured for production, violating the principle of least privilege.
**Prevention:** Always use a configurable list of allowed origins (e.g., via environment variables) and explicitly restrict CORS to known trusted domains.

## 2024-05-24 - Command Argument Injection Risk
**Vulnerability:** A subprocess call to `beet` used a user-controlled file path as the final positional argument without `--`.
**Learning:** If a file was named starting with a hyphen (e.g., `-h` or `--delete`), the executable would interpret it as a command-line flag rather than a file path.
**Prevention:** Always use `--` to indicate the end of command options before passing untrusted or dynamic file paths to external commands.
