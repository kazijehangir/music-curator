def sanitize_pb_filter(value: str) -> str:
    """
    Safely escapes strings for PocketBase query construction in Python.
    Backslashes first, then single quotes.
    """
    if not value:
        return ""
    # Escape backslashes first, then escape single quotes.
    return str(value).replace('\\', '\\\\').replace("'", "\\'")
