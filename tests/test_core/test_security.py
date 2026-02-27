
import pytest
from src.core.security import sanitize_pb_filter

def test_sanitize_pb_filter_simple_string():
    """Simple strings should remain unchanged."""
    assert sanitize_pb_filter("simple") == "simple"

def test_sanitize_pb_filter_quotes():
    """Single quotes should be escaped."""
    assert sanitize_pb_filter("O'Reilly") == "O\\'Reilly"
    assert sanitize_pb_filter("'start") == "\\'start"
    assert sanitize_pb_filter("end'") == "end\\'"

def test_sanitize_pb_filter_backslashes():
    """Backslashes should be doubled."""
    assert sanitize_pb_filter("C:\\Music") == "C:\\\\Music"
    assert sanitize_pb_filter("\\leading") == "\\\\leading"

def test_sanitize_pb_filter_injection_attempt():
    """
    Injection attempts combining backslashes and quotes must be handled safely.

    If the input is `hack\'`, a naive replace("'", "\'") would produce `hack\\'`.
    PocketBase parser would see `hack\\` (escaped backslash) followed by `'` (closing quote).
    This allows the attacker to break out of the string literal.

    Correct sanitization should produce `hack\\\\\'`.
    PocketBase parser sees `hack\\` (escaped backslash) and `\'` (escaped quote).
    The literal value becomes `hack\'`.
    """
    # The attacker tries to end the string with an escaped backslash, exposing the quote
    injection = "hack\\'"
    sanitized = sanitize_pb_filter(injection)

    # We expect backslash to be doubled, then quote escaped
    # "hack" + "\\" -> "\\\\" + "'" -> "\\'"
    expected = "hack\\\\\\'"
    assert sanitized == expected

def test_sanitize_pb_filter_mixed():
    """Mix of quotes and backslashes."""
    input_str = "Artist's \\ Album"
    # Expected: Artist\'s \\\\ Album
    assert sanitize_pb_filter(input_str) == "Artist\\'s \\\\ Album"

def test_sanitize_pb_filter_empty():
    assert sanitize_pb_filter("") == ""
    assert sanitize_pb_filter(None) == ""
