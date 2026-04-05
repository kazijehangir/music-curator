from src.core.security import sanitize_pb_filter

def test_sanitize_pb_filter():
    # Should escape backslashes first, then single quotes
    # Original: foo'bar\baz
    # Expected: foo\'bar\\baz
    assert sanitize_pb_filter("foo'bar\\baz") == "foo\\'bar\\\\baz"
    assert sanitize_pb_filter("normal_string") == "normal_string"
    assert sanitize_pb_filter("only'quotes'") == "only\\'quotes\\'"
    assert sanitize_pb_filter("only\\backslashes\\") == "only\\\\backslashes\\\\"
