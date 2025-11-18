"""Tests for the Kimi CLI plain text parser."""

import pytest

from clink.parsers.base import ParserError
from clink.parsers.kimi import KimiPlainParser


def test_kimi_parser_extracts_textpart():
    """Test that kimi parser extracts TextPart content."""
    parser = KimiPlainParser()
    stdout = """hello
StepBegin(n=1)
ThinkPart(type='think', think='The user said "hello" which is a simple greeting.')
TextPart(type='text', text="Hello! I'm Kimi CLI, ready to help you.")
StatusUpdate(status=StatusSnapshot(context_usage=0.02))"""

    parsed = parser.parse(stdout=stdout, stderr="")

    assert "Hello! I'm Kimi CLI" in parsed.content
    assert "thinking" in parsed.metadata
    assert len(parsed.metadata["thinking"]) > 0


def test_kimi_parser_simple_output():
    """Test that kimi parser handles simple plain text output."""
    parser = KimiPlainParser()
    stdout = "Hello! I'm here to help you with software development tasks."

    parsed = parser.parse(stdout=stdout, stderr="")

    assert parsed.content == "Hello! I'm here to help you with software development tasks."


def test_kimi_parser_multiple_textparts():
    """Test that kimi parser combines multiple TextPart entries."""
    parser = KimiPlainParser()
    stdout = """StepBegin(n=1)
TextPart(type='text', text="First part.")
TextPart(type='text', text="Second part.")
StepEnd()"""

    parsed = parser.parse(stdout=stdout, stderr="")

    assert "First part." in parsed.content
    assert "Second part." in parsed.content


def test_kimi_parser_empty_output():
    """Test that kimi parser raises error on empty output."""
    parser = KimiPlainParser()

    with pytest.raises(ParserError, match="empty stdout"):
        parser.parse(stdout="", stderr="")


def test_kimi_parser_with_stderr():
    """Test that kimi parser includes stderr in metadata."""
    parser = KimiPlainParser()
    stdout = "Hello!"
    stderr = "Warning: something happened"

    parsed = parser.parse(stdout=stdout, stderr=stderr)

    assert parsed.content == "Hello!"
    assert parsed.metadata["stderr"] == stderr


def test_kimi_parser_mixed_format():
    """Test kimi parser with mixed structured and plain text."""
    parser = KimiPlainParser()
    stdout = """User input: test
StepBegin(n=1)
ThinkPart(type='think', think='Processing request')
TextPart(type='text', text="Here is the response")
Plain text line
StatusUpdate(status=StatusSnapshot())"""

    parsed = parser.parse(stdout=stdout, stderr="")

    # Should extract TextPart content
    assert "Here is the response" in parsed.content


def test_kimi_parser_fallback_to_all_stdout():
    """Test that parser falls back to full stdout if no TextPart found."""
    parser = KimiPlainParser()
    stdout = """No structured parts here
Just plain text
Multiple lines"""

    parsed = parser.parse(stdout=stdout, stderr="")

    assert "No structured parts" in parsed.content
    assert "Just plain text" in parsed.content
