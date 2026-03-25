from src.core.security import sanitize_pb_filter

def test_sanitize_pb_filter_empty_string():
    assert sanitize_pb_filter("") == ""

def test_sanitize_pb_filter_normal_string():
    assert sanitize_pb_filter("hello world") == "hello world"

def test_sanitize_pb_filter_escapes_single_quotes():
    assert sanitize_pb_filter("O'Reilly") == "O\\'Reilly"
    assert sanitize_pb_filter("'quotes'") == "\\'quotes\\'"

def test_sanitize_pb_filter_escapes_backslashes():
    assert sanitize_pb_filter("C:\\path\\to\\file") == "C:\\\\path\\\\to\\\\file"

def test_sanitize_pb_filter_escapes_both():
    assert sanitize_pb_filter("C:\\path\\to\\O'Reilly's\\file") == "C:\\\\path\\\\to\\\\O\\'Reilly\\'s\\\\file"
