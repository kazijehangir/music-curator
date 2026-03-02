from src.core.security import sanitize_pb_filter

def test_sanitize_pb_filter_basic():
    """Basic strings are unaffected."""
    assert sanitize_pb_filter("hello") == "hello"

def test_sanitize_pb_filter_single_quote():
    """Single quotes are escaped."""
    assert sanitize_pb_filter("O'Reilly") == "O\\'Reilly"

def test_sanitize_pb_filter_backslash():
    """Backslashes are escaped."""
    assert sanitize_pb_filter("C:\\path\\to") == "C:\\\\path\\\\to"

def test_sanitize_pb_filter_injection():
    """Strings with both backslashes and single quotes are safely escaped."""
    # Exploit scenario: foo\'bar
    # If we only replace ' with \', foo\'bar becomes foo\\'bar
    # In PocketBase, \\' evaluates to a literal backslash followed by an unescaped quote, breaking the filter.
    # We must escape \ to \\ first, then ' to \'.
    # So foo\'bar -> foo\\\'bar
    assert sanitize_pb_filter("foo\\'bar") == "foo\\\\\\'bar"
