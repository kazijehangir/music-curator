def sanitize_pb_filter(value: str) -> str:
    """
    Safely escapes a string for use in PocketBase filters.
    Replaces backslashes first to prevent injection via trailing backslash,
    then escapes single quotes.
    """
    return value.replace('\\', '\\\\').replace("'", "\\'")
