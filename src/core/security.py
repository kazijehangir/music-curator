def sanitize_pb_filter(value: str) -> str:
    """
    Safely escapes a string for use in PocketBase filter expressions.

    PocketBase filter strings must have single quotes escaped as \',
    but before that, existing backslashes must be escaped to avoid injection
    via unhandled backslashes (e.g. escaping the escaping backslash).
    """
    if value is None:
        return ""

    # 1. Escape existing backslashes first
    value = str(value).replace("\\", "\\\\")

    # 2. Escape single quotes
    return value.replace("'", "\\'")
