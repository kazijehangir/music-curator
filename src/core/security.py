"""
Security utilities for the Music Curator application.
"""

def sanitize_pb_filter(value: str) -> str:
    """
    Sanitize a string value for use in a PocketBase filter string.

    PocketBase filters use single quotes. To prevent injection:
    1. Escape backslashes first (to prevent escaping the quote escape).
    2. Escape single quotes.

    Args:
        value: The raw string value (e.g., a filename or user input).

    Returns:
        A sanitized string safe to embed in a filter like f"field='{sanitized}'".
    """
    if not isinstance(value, str):
        return str(value)

    return value.replace('\\', '\\\\').replace("'", "\\'")
