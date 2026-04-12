from src.core.security import sanitize_pb_filter

def test_sanitize_pb_filter():
    assert sanitize_pb_filter("a'b") == "a\\'b"
    assert sanitize_pb_filter("a\\b") == "a\\\\b"
    assert sanitize_pb_filter("a\\'b") == "a\\\\\\'b"
