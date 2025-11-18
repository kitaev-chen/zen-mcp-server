"""Tests for the iflow CLI plain text parser."""

import pytest

from clink.parsers.base import ParserError
from clink.parsers.iflow import IflowPlainParser


def test_iflow_parser_extracts_content_before_execution_info():
    """Test that iflow parser extracts the main content before execution info."""
    parser = IflowPlainParser()
    stdout = """4

What else can I do for you?

<Execution Info>
{
  "session-id": "session-f9a82a95-c9c4-40d8-804d-e64fc8d6e46e",
  "conversation-id": "d28091c3-553b-4ee8-bba2-2a7fedb9cc6c",
  "assistantRounds": 1,
  "executionTimeMs": 7948,
  "tokenUsage": {
    "input": 17330,
    "output": 2,
    "total": 17332
  }
}
</Execution Info>"""

    parsed = parser.parse(stdout=stdout, stderr="")

    assert "4" in parsed.content
    assert "What else can I do for you?" in parsed.content
    assert "Execution Info" not in parsed.content
    assert parsed.metadata.get("execution_info") is not None
    assert parsed.metadata["execution_info"]["assistantRounds"] == 1
    assert parsed.metadata["usage"]["input"] == 17330
    assert parsed.metadata["usage"]["output"] == 2


def test_iflow_parser_handles_output_without_execution_info():
    """Test that iflow parser works without execution info section."""
    parser = IflowPlainParser()
    stdout = "The answer is 42.\n\nAnything else?"

    parsed = parser.parse(stdout=stdout, stderr="")

    assert parsed.content == "The answer is 42.\n\nAnything else?"
    assert "execution_info" not in parsed.metadata


def test_iflow_parser_requires_output():
    """Test that iflow parser raises error on empty output."""
    parser = IflowPlainParser()

    with pytest.raises(ParserError, match="empty stdout"):
        parser.parse(stdout="", stderr="")


def test_iflow_parser_handles_only_whitespace():
    """Test that iflow parser raises error on whitespace-only output."""
    parser = IflowPlainParser()

    with pytest.raises(ParserError, match="empty stdout"):
        parser.parse(stdout="   \n\n  ", stderr="")


def test_iflow_parser_captures_stderr():
    """Test that iflow parser includes stderr in metadata."""
    parser = IflowPlainParser()
    stdout = "Response text"
    stderr = "Warning: something happened"

    parsed = parser.parse(stdout=stdout, stderr=stderr)

    assert parsed.content == "Response text"
    assert parsed.metadata["stderr"] == stderr


def test_iflow_parser_handles_malformed_execution_info():
    """Test that parser handles malformed execution info gracefully."""
    parser = IflowPlainParser()
    stdout = """Here is the response.

<Execution Info>
This is not valid JSON!
</Execution Info>"""
    
    parsed = parser.parse(stdout=stdout, stderr="")
    
    assert parsed.content == "Here is the response."
    assert "execution_info" not in parsed.metadata


def test_iflow_parser_filters_windows_path_warning():
    """Test that parser filters out Windows path warnings from stderr."""
    parser = IflowPlainParser()
    stdout = "Understood. I'm ready to help with your repository tasks."
    stderr = "The system cannot find the path specified.\r\n"
    
    parsed = parser.parse(stdout=stdout, stderr=stderr)
    
    assert parsed.content == "Understood. I'm ready to help with your repository tasks."
    # Windows path warning should be filtered out
    assert "stderr" not in parsed.metadata or parsed.metadata["stderr"] is None
