"""
Security utilities for music-curator.
"""

def sanitize_pb_filter(value: str) -> str:
    """
    Sanitizes a string for use in a PocketBase filter query.

    PocketBase filters use single quotes for string literals. To prevent
    injection, we must escape single quotes. However, backslashes are also
    escape characters, so we must escape them first to prevent an attacker
    from escaping the closing quote.

    Example:
        Input:  foo'bar
        Output: foo\'bar

        Input:  C:\\Music
        Output: C:\\\\Music

        Input:  hack\\'
        Output: hack\\\\\\'  (PocketBase sees: hack\' inside the string)
    """
    if not value:
        return ""

    # 1. Escape backslashes first (so they don't escape our subsequent escapes)
    # 2. Escape single quotes
    return value.replace("\\", "\\\\").replace("'", "\\'")
