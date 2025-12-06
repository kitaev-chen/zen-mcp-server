"""Parser for Kimi CLI plain text output."""

from __future__ import annotations

import re
from typing import Any

from .base import BaseParser, ParsedCLIResponse, ParserError


# Markers that indicate start of Kimi's structured output (skip everything before)
STRUCTURED_OUTPUT_MARKERS = [
    "StepBegin(",
    "ThinkPart(",
    "TextPart(",
    "ToolCall(",
    "StatusUpdate(",
    "type='think'",
    "type='text'",
]

# Lines to skip entirely (tool calls, results, status updates)
SKIP_LINE_MARKERS = [
    "StepBegin(",
    "StepEnd(",
    "StatusUpdate(",
    "ToolCall(",
    "ToolResult(",
    "FunctionBody(",
    "ToolOk(",
    "ToolError(",
]


class KimiPlainParser(BaseParser):
    """Parse plain text output produced by `kimi --print --command`.
    
    Kimi CLI in --print mode outputs:
    1. Echo of the input prompt (system prompt + user request) - SKIP THIS
    2. Structured parts (ThinkPart, ToolCall, ToolResult, TextPart, StatusUpdate)
    
    We only extract TextPart content as the main response, skipping:
    - The echoed prompt
    - ToolCall/ToolResult traces
    - StatusUpdate lines
    
    Example output to parse:
        [echoed system prompt - SKIP]
        [echoed user request - SKIP]
        StepBegin(n=1)
        ThinkPart(type='think', think='analyzing...')
        ToolCall(type='function', id='...', function=FunctionBody(...))  - SKIP
        ToolResult(tool_call_id='...', result=ToolOk(...))  - SKIP
        TextPart(type='text', text="Here is my analysis...")  - EXTRACT THIS
        StatusUpdate(status=StatusSnapshot(...))  - SKIP
    """

    name = "kimi_plain"

    def parse(self, stdout: str, stderr: str) -> ParsedCLIResponse:
        if not stdout.strip():
            raise ParserError("Kimi CLI returned empty stdout")

        lines = stdout.strip().splitlines()
        
        # Step 1: Find where structured output begins (skip echoed prompt)
        structured_start = 0
        for i, line in enumerate(lines):
            if any(marker in line for marker in STRUCTURED_OUTPUT_MARKERS):
                structured_start = i
                break
        
        # Step 2: Extract TextPart content from structured section only
        text_parts: list[str] = []
        
        for line in lines[structured_start:]:
            # Skip tool calls, results, status updates
            if any(marker in line for marker in SKIP_LINE_MARKERS):
                continue
            
            # Extract TextPart content
            if "TextPart(" in line and "text=" in line:
                text_content = self._extract_quoted_value(line, "text=")
                if text_content:
                    text_parts.append(text_content)
        
        # Step 3: Build content
        if text_parts:
            content = " ".join(text_parts)
        else:
            # Fallback: If no TextPart found, try plain text after structured start
            # (for simpler Kimi outputs without --print mode)
            plain_lines = []
            for line in lines[structured_start:]:
                if not any(marker in line for marker in SKIP_LINE_MARKERS + STRUCTURED_OUTPUT_MARKERS):
                    if line.strip():
                        plain_lines.append(line.strip())
            content = "\n".join(plain_lines) if plain_lines else ""
        
        # Ultimate fallback: if nothing extracted, use raw stdout (but warn)
        if not content or len(content) < 20:
            # Last resort - might include noise but at least returns something
            content = stdout.strip()
        
        if not content:
            raise ParserError("Kimi CLI output did not contain extractable content")
        
        metadata: dict[str, Any] = {"raw_stdout": stdout}
        
        # Extract thinking content for metadata (from structured section only)
        think_parts: list[str] = []
        for line in lines[structured_start:]:
            if "ThinkPart(" in line and "think=" in line:
                think_content = self._extract_quoted_value(line, "think=")
                if think_content:
                    think_parts.append(think_content)
        
        if think_parts:
            metadata["thinking"] = think_parts
        
        if stderr and stderr.strip():
            metadata["stderr"] = stderr.strip()
        
        return ParsedCLIResponse(content=content, metadata=metadata)

    def _extract_quoted_value(self, line: str, prefix: str) -> str | None:
        """Extract value after prefix= from a line, handling quoted strings.
        
        Example: _extract_quoted_value('TextPart(text="hello world")', 'text=')
        Returns: 'hello world'
        """
        start = line.find(prefix)
        if start == -1:
            return None
        
        rest = line[start + len(prefix):]
        if not rest or rest[0] not in "\"'":
            return None
        
        quote = rest[0]
        chars = []
        i = 1
        while i < len(rest):
            if rest[i] == quote and (i == 0 or rest[i - 1] != "\\"):
                break
            chars.append(rest[i])
            i += 1
        
        return "".join(chars) if chars else None
