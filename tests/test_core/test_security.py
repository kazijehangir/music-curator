from src.core.security import sanitize_pb_filter

def test_sanitize_pb_filter_normal_string():
    assert sanitize_pb_filter("normal string") == "normal string"

def test_sanitize_pb_filter_single_quote():
    assert sanitize_pb_filter("O'Reilly") == "O\\'Reilly"

def test_sanitize_pb_filter_backslash():
    assert sanitize_pb_filter("C:\\path\\to\\file") == "C:\\\\path\\\\to\\\\file"

def test_sanitize_pb_filter_backslash_and_quote():
    # If the user inputs a backslash followed by a quote: \"'
    # Without escaping the backslash first, replacing only the quote yields: \"\\'
    # In many parsers, the \" escapes the backslash, leaving the quote unescaped.
    # By escaping both (backslashes first), we get \\\\\\' which escapes both safely.
    assert sanitize_pb_filter("file\\'name") == "file\\\\\\'name"

def test_sanitize_pb_filter_empty_string():
    assert sanitize_pb_filter("") == ""
