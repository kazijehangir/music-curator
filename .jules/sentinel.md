## 2025-03-11 - Command Argument Injection in beet subprocess
**Vulnerability:** Subprocess command execution in `src/services/tagging.py` passed user-controlled file paths as arguments to `beet import` without the `--` separator.
**Learning:** This allowed argument injection, where paths starting with a hyphen (e.g., `-invalid_arg.opus`) could be misinterpreted as command-line flags.
**Prevention:** When executing external CLI commands (like `beet`) via `subprocess.run` with user-controlled file paths, always include the `--` separator before the positional path argument to ensure any leading hyphens in the path are strictly treated as positional file paths rather than executable arguments.
