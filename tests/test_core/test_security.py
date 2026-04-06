from src.core.security import sanitize_pb_filter

def test_sanitize_pb_filter_normal_string():
    assert sanitize_pb_filter("normal string") == "normal string"

def test_sanitize_pb_filter_single_quote():
    assert sanitize_pb_filter("O'Reilly") == "O\\'Reilly"

def test_sanitize_pb_filter_backslash():
    assert sanitize_pb_filter("C:\\Windows\\Path") == "C:\\\\Windows\\\\Path"

def test_sanitize_pb_filter_mixed():
    assert sanitize_pb_filter("C:\\Users\\O'Reilly") == "C:\\\\Users\\\\O\\'Reilly"

def test_sanitize_pb_filter_non_string():
    assert sanitize_pb_filter(123) == 123
    assert sanitize_pb_filter(None) is None
