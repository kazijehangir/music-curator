from src.core.security import sanitize_pb_filter

def test_sanitize_pb_filter_single_quote():
    assert sanitize_pb_filter("O'Connor") == "O\\'Connor"

def test_sanitize_pb_filter_backslash():
    assert sanitize_pb_filter("path\\to\\file") == "path\\\\to\\\\file"

def test_sanitize_pb_filter_combined_injection():
    # If backslash isn't escaped first, an attacker can input \', which becomes \\'
    # Then PocketBase parser sees the escaped backslash \\ and an UNESCAPED single quote '
    assert sanitize_pb_filter("injection\\'") == "injection\\\\\\'"

def test_sanitize_pb_filter_no_special_chars():
    assert sanitize_pb_filter("normal string") == "normal string"

def test_sanitize_pb_filter_empty_string():
    assert sanitize_pb_filter("") == ""
