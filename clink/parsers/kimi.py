"""Parser for Kimi CLI plain text output."""

from __future__ import annotations

import re
from typing import Any

from .base import BaseParser, ParsedCLIResponse, ParserError


class KimiPlainParser(BaseParser):
    """Parse plain text output produced by `kimi --print --thinking --command`.
    
    Kimi CLI outputs a mix of structured parts (StepBegin, ThinkPart, TextPart, StatusUpdate)
    and plain text. We extract the TextPart content as the main response.
    
    Example output:
        hello
        StepBegin(n=1)
        ThinkPart(type='think', think='...')
        TextPart(type='text', text="Hello! I'm Kimi CLI...")
        StatusUpdate(status=StatusSnapshot(...))
    
    In simpler cases without --print:
        Hello! I'm here to help you...
    """

    name = "kimi_plain"

    def parse(self, stdout: str, stderr: str) -> ParsedCLIResponse:
        if not stdout.strip():
            raise ParserError("Kimi CLI returned empty stdout")

        lines = stdout.strip().splitlines()
        
        # Try to extract TextPart content
        text_parts: list[str] = []
        plain_text_lines: list[str] = []
        
        for line in lines:
            # Look for TextPart(type='text', text="...")
            # Match text content between quotes, handling escaped quotes and quotes within the string
            text_match = re.search(r"TextPart\([^)]*text=['\"](.+?)['\"]\)", line)
            if text_match:
                text_parts.append(text_match.group(1))
            # Collect lines that don't look like structured parts
            elif not any(keyword in line for keyword in [
                "StepBegin", "ThinkPart", "TextPart", "StatusUpdate",
                "StepEnd", "ToolCallPart"
            ]):
                if line.strip():
                    plain_text_lines.append(line.strip())
        
        # Prefer TextPart content if available
        if text_parts:
            content = " ".join(text_parts)
        elif plain_text_lines:
            content = "\n".join(plain_text_lines)
        else:
            # Fallback: use all stdout
            content = stdout.strip()
        
        if not content:
            raise ParserError("Kimi CLI output did not contain extractable content")
        
        metadata: dict[str, Any] = {"raw_stdout": stdout}
        
        # Try to extract thinking content for metadata
        think_parts: list[str] = []
        for line in lines:
            think_match = re.search(r"ThinkPart\([^)]*think=['\"](.+?)['\"]\)", line)
            if think_match:
                think_parts.append(think_match.group(1))
        
        if think_parts:
            metadata["thinking"] = think_parts
        
        if stderr and stderr.strip():
            metadata["stderr"] = stderr.strip()
        
        return ParsedCLIResponse(content=content, metadata=metadata)
