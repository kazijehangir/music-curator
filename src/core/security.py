def sanitize_pb_filter(value: str) -> str:
    """
    Safely escape strings for PocketBase string literal filters.
    Replaces backslashes with double backslashes, then single quotes with escaped single quotes.
    """
    if not isinstance(value, str):
        return str(value)

    # 1. Escape existing backslashes first so we don't double-escape our quote escapes
    value = value.replace("\\", "\\\\")

    # 2. Escape single quotes used for wrapping string literals
    value = value.replace("'", "\\'")

    return value
