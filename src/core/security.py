def sanitize_pb_filter(value: str) -> str:
    """
    Safely escapes strings for use in PocketBase filter queries.
    Prevents filter injection by escaping backslashes first, then single quotes.
    Because the Python SDK lacks parameter binding (unlike JS pb.filter),
    this manual sanitization is required.
    """
    if not value:
        return ""
    # 1. Escape literal backslashes to prevent bypassing the quote escape
    val = value.replace("\\", "\\\\")
    # 2. Escape single quotes (the string delimiter in PocketBase filters)
    val = val.replace("'", "\\'")
    return val
