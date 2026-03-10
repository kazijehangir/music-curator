
## 2024-05-24 - [Command Argument Injection in subprocess]
**Vulnerability:** Command argument injection vulnerability when passing user-controlled file paths to `subprocess.run` (e.g., `beet import`) without a `--` separator.
**Learning:** Paths starting with hyphens can be misinterpreted as malicious command-line flags.
**Prevention:** Always use the `--` separator before positional arguments like file paths when running external CLI commands via `subprocess.run`.
