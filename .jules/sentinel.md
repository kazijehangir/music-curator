## 2025-03-19 - Command Argument Injection in External Subprocess Calls
**Vulnerability:** External command tools invoked via `subprocess.run` (e.g., `beet`) used direct string injection for user-controlled file paths.
**Learning:** This exposes the application to command argument injection. File paths starting with a hyphen (e.g., `-V.mp3`) can be misinterpreted by the external command as a flag instead of a positional file path, leading to unintended and potentially malicious behavior.
**Prevention:** Always use the `--` separator before positional file paths in `subprocess` call argument lists to explicitly denote the end of command options.
