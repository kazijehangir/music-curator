## 2026-03-21 - [Path Argument Injection in External CLI Commands]
**Vulnerability:** Command injection risk via unsanitized file paths (e.g., `-v`) being interpreted as options/flags by the `beet` CLI tool in `subprocess.run()`.
**Learning:** Even when `shell=False` is used, if the positional arguments are directly appended without an argument separator, commands may misinterpret user-controlled input (like file names starting with a hyphen) as options, leading to unexpected behavior or potential command injection depending on the CLI tool capabilities.
**Prevention:** Always use the `--` argument separator before passing user-controlled file paths or arguments to external CLI commands via `subprocess.run()`.
