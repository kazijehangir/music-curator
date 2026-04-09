from src.core.security import sanitize_pb_filter

def test_sanitize_pb_filter_normal_string():
    assert sanitize_pb_filter("normal") == "normal"

def test_sanitize_pb_filter_single_quote():
    assert sanitize_pb_filter("O'Reilly") == "O\\'Reilly"

def test_sanitize_pb_filter_backslash():
    assert sanitize_pb_filter("C:\\path") == "C:\\\\path"

def test_sanitize_pb_filter_backslash_and_quote():
    # If the user tries to escape the quote themselves, we must escape their backslash
    # as well as the quote, resulting in \\\'
    assert sanitize_pb_filter("C:\\path\\'to") == "C:\\\\path\\\\\\'to"

def test_sanitize_pb_filter_trailing_backslash():
    # A trailing backslash could escape the enclosing quote in PocketBase if not handled
    assert sanitize_pb_filter("trailing\\") == "trailing\\\\"
