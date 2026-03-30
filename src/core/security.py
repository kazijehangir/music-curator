def sanitize_pb_filter(value: str) -> str:
    """
    Safely escapes a string for interpolation into a PocketBase filter query.

    The Python SDK lacks the JS SDK's `pb.filter()` parameter binding, meaning
    we must construct filter strings manually. Because PocketBase filters use
    single quotes for strings, we must escape single quotes. However, we must
    ALSO escape backslashes first, otherwise an attacker could input a string
    ending with a backslash before a single quote (e.g., `\\`), which would
    escape our inserted backslash (`\\'`), leaving the original single quote
    active and allowing filter injection.
    """
    # 1. Escape backslashes first (so they don't escape our later quote-escapes)
    escaped_backslashes = value.replace("\\", "\\\\")

    # 2. Escape single quotes (PocketBase requires escaping single quotes)
    return escaped_backslashes.replace("'", "\\'")
