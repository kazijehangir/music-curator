## 2025-03-07 - [Command Argument Injection & Permissive CORS]
**Vulnerability:**
1. The `subprocess.run` call in `src/services/tagging.py` passed `str(file_path)` directly to the `beet import` command, which could be exploited if a malicious file started with a hyphen (Command Argument Injection).
2. The `allow_origins` in `src/api/main.py` was hardcoded to `["*"]`, which is overly permissive.
**Learning:**
1. Even when using an argument list instead of `shell=True`, positional file paths must be isolated from command flags to prevent argument injection.
2. CORS configurations should be securely restricted using environment variables rather than hardcoded permissive arrays.
**Prevention:**
1. Always include the `--` separator before the positional path argument in external CLI commands.
2. Explicitly restrict `CORS_ORIGINS` via environment variable and parse it securely in middleware.
