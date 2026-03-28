import pytest
from src.core.security import sanitize_pb_filter

def test_sanitize_pb_filter_empty():
    assert sanitize_pb_filter("") == ""
    assert sanitize_pb_filter(None) == ""

def test_sanitize_pb_filter_normal_string():
    assert sanitize_pb_filter("hello world") == "hello world"

def test_sanitize_pb_filter_single_quotes():
    assert sanitize_pb_filter("don't") == "don\\'t"

def test_sanitize_pb_filter_backslashes():
    assert sanitize_pb_filter("C:\\Windows\\System32") == "C:\\\\Windows\\\\System32"

def test_sanitize_pb_filter_combined_injection():
    # If a user provides an input like `\' OR 1=1`, replacing only quotes
    # yields `\\' OR 1=1`, which escapes the backslash instead of the quote.
    # By replacing backslashes first, it yields `\\\' OR 1=1`, keeping the quote literal.
    malicious_input = "\\' OR 1=1"
    escaped = sanitize_pb_filter(malicious_input)
    assert escaped == "\\\\\\' OR 1=1"
