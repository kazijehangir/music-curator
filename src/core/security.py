def sanitize_pb_filter(value: str) -> str:
    """
    Sanitizes strings for safe use inside PocketBase single-quoted filter strings.
    Escapes backslashes first, then single quotes, to prevent filter injection.
    """
    return value.replace('\\', '\\\\').replace("'", "\\'")
