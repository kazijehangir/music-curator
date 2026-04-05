def sanitize_pb_filter(value: str) -> str:
    """Safely escapes strings for PocketBase query construction."""
    return value.replace("\\", "\\\\").replace("'", "\\'")
