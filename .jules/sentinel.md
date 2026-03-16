## 2024-05-18 - Command Argument Injection in Subprocess
**Vulnerability:** Command argument injection vulnerability existed in `src/services/tagging.py` where a user-controlled file path from the database was passed to `subprocess.run(["beet", "import", ... , file_path])` without the `--` separator.
**Learning:** If a file path starts with a hyphen (e.g., `-foo`), the `beet` command-line tool might interpret it as a flag instead of a positional file path argument, potentially leading to arbitrary command execution or unexpected behavior.
**Prevention:** Always use the `--` argument separator when passing user-controlled file paths to external commands via `subprocess.run` to ensure they are strictly treated as positional arguments.
