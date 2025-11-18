"""Tests for the vecli CLI plain text parser."""

import pytest

from clink.parsers.base import ParserError
from clink.parsers.vecli import VecliPlainParser


def test_vecli_parser_extracts_plain_text():
    """Test that vecli parser extracts plain text content."""
    parser = VecliPlainParser()
    stdout = "The answer is 4."

    parsed = parser.parse(stdout=stdout, stderr="")

    assert parsed.content == "The answer is 4."
    assert "raw_stdout" in parsed.metadata


def test_vecli_parser_handles_summary_tag():
    """Test that vecli parser extracts SUMMARY with spaces."""
    parser = VecliPlainParser()
    stdout = """Response content here.

< SUMMARY >
This is a summary with spaces.
</SUMMARY >"""

    parsed = parser.parse(stdout=stdout, stderr="")

    assert "Response content here" in parsed.content
    assert parsed.metadata["summary"] == "This is a summary with spaces."


def test_vecli_parser_handles_summary_without_spaces():
    """Test that vecli parser also handles SUMMARY without spaces."""
    parser = VecliPlainParser()
    stdout = """Response content.

<SUMMARY>
Summary without spaces.
</SUMMARY>"""

    parsed = parser.parse(stdout=stdout, stderr="")

    assert "Response content" in parsed.content
    assert parsed.metadata["summary"] == "Summary without spaces."


def test_vecli_parser_handles_no_summary():
    """Test that vecli parser works without SUMMARY tag."""
    parser = VecliPlainParser()
    stdout = "Just plain response content."

    parsed = parser.parse(stdout=stdout, stderr="")

    assert parsed.content == "Just plain response content."
    assert "summary" not in parsed.metadata


def test_vecli_parser_requires_output():
    """Test that vecli parser raises error on empty output."""
    parser = VecliPlainParser()

    with pytest.raises(ParserError, match="empty stdout"):
        parser.parse(stdout="", stderr="")


def test_vecli_parser_detects_non_text_parts():
    """Test that vecli parser detects non-text parts in stderr."""
    parser = VecliPlainParser()
    stdout = "Response content"
    stderr = "there are non-text parts functionCall in the response"

    parsed = parser.parse(stdout=stdout, stderr=stderr)

    assert parsed.metadata["has_non_text_parts"] is True
    assert parsed.metadata["has_function_calls"] is True


def test_vecli_parser_handles_normal_stderr():
    """Test that vecli parser handles normal stderr without special markers."""
    parser = VecliPlainParser()
    stdout = "Response"
    stderr = "Some warning message"

    parsed = parser.parse(stdout=stdout, stderr=stderr)

    assert parsed.metadata["stderr"] == stderr
    assert "has_non_text_parts" not in parsed.metadata


def test_vecli_parser_captures_stderr():
    """Test that vecli parser includes stderr in metadata."""
    parser = VecliPlainParser()
    stdout = "Hello"
    stderr = "Warning: deprecated API usage"

    parsed = parser.parse(stdout=stdout, stderr=stderr)

    assert parsed.content == "Hello"
    assert parsed.metadata["stderr"] == stderr


def test_vecli_parser_preserves_full_content():
    """Test that vecli parser preserves the full content including SUMMARY."""
    parser = VecliPlainParser()
    stdout = """Response line 1
Response line 2

< SUMMARY >
Short summary
</SUMMARY >"""

    parsed = parser.parse(stdout=stdout, stderr="")

    # Full content is preserved
    assert "Response line 1" in parsed.content
    assert "Response line 2" in parsed.content
    assert "< SUMMARY >" in parsed.content
    # Summary is also extracted to metadata
    assert parsed.metadata["summary"] == "Short summary"
