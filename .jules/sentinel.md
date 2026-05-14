## 2024-05-24 - Command Argument Injection in Subprocess Calls
**Vulnerability:** Command argument injection risk in `src/services/tagging.py` where a user-controlled file path from the database was passed directly to `beet import` via `subprocess.run` without a POSIX `--` separator.
**Learning:** Files with names starting with hyphens (e.g., `-h`, `--move`) are misinterpreted as command-line flags rather than positional file arguments by the executed command, potentially leading to unauthorized execution paths or errors.
**Prevention:** Always use the `--` POSIX separator in `subprocess.run` argument lists immediately preceding user-controlled or dynamically generated file paths to ensure they are strictly treated as positional arguments.
