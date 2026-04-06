def sanitize_pb_filter(value: str) -> str:
    """
    Safely escape a string for use in a PocketBase query filter.
    Backslashes must be escaped first, then single quotes.
    """
    if not isinstance(value, str):
        return value
    return value.replace('\\', '\\\\').replace("'", "\\'")
