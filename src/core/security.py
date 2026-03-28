def sanitize_pb_filter(value: str) -> str:
    """
    Safely escapes strings for PocketBase query construction in Python.
    Manual single quote escaping (e.g., `.replace("'", "\\'")`) is insufficient
    for security and leads to filter injection, particularly due to unhandled backslashes.
    """
    if not value:
        return ""
    # Always escape backslashes first, then single quotes
    return str(value).replace('\\', '\\\\').replace("'", "\\'")
