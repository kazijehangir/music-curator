def sanitize_pb_filter(value: str) -> str:
    """
    Safely escapes strings for PocketBase query construction.
    Escapes backslashes first, then single quotes to prevent filter injection.
    """
    return value.replace('\\', '\\\\').replace("'", "\\'")
