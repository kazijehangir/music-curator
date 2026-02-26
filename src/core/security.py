def sanitize_pb_filter(value: str) -> str:
    """
    Sanitizes a string for use in a PocketBase filter.

    Escapes backslashes first, then single quotes, to prevent injection attacks.
    If backslashes are not escaped, they can escape the escaped single quote,
    leading to a filter injection vulnerability.

    Example:
        Input:  foo\'bar
        Unsafe: foo\\'bar (PocketBase sees: foo, then escaped quote -> quote) -> 'foo'bar...
        Safe:   foo\\\'bar (PocketBase sees: foo, escaped backslash -> \, escaped quote -> ') -> 'foo\'bar'
    """
    if not isinstance(value, str):
        return str(value)

    return value.replace('\\', '\\\\').replace("'", "\\'")
