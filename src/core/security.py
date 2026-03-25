def sanitize_pb_filter(value: str) -> str:
    """
    Safely escapes strings for PocketBase query construction in Python.
    Because the Python SDK lacks the JS SDK's parameter binding (`pb.filter()`),
    we must manually escape backslashes first, then single quotes to prevent
    filter injection vulnerabilities.
    """
    # Order is critical: backslashes must be escaped before quotes,
    # otherwise we'd double-escape the backslashes added to the quotes.
    safe_value = value.replace("\\", "\\\\")
    safe_value = safe_value.replace("'", "\\'")
    return safe_value
