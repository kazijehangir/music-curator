def sanitize_pb_filter(value: str) -> str:
    """
    Safely escapes a string for use in PocketBase filter queries.
    Replaces backslashes first, then single quotes.
    """
    if not isinstance(value, str):
        return value
    return value.replace("\\", "\\\\").replace("'", "\\'")
