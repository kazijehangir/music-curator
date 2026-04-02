import pytest
from src.core.security import sanitize_pb_filter

def test_sanitize_pb_filter():
    assert sanitize_pb_filter(None) == ""
    assert sanitize_pb_filter("hello") == "hello"
    assert sanitize_pb_filter("O'Reilly") == "O\\'Reilly"
    assert sanitize_pb_filter("C:\\path\\file.txt") == "C:\\\\path\\\\file.txt"
    assert sanitize_pb_filter("Injection\\' OR 1=1") == "Injection\\\\\\' OR 1=1"
