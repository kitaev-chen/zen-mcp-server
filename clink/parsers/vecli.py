"""Parser for vecli CLI plain text output."""

from __future__ import annotations

import re
from typing import Any

from .base import BaseParser, ParsedCLIResponse, ParserError


class VecliPlainParser(BaseParser):
    """Parse plain text stdout produced by vecli CLI.
    
    vecli outputs the response in plain text to stdout, often with a SUMMARY section.
    Similar to iflow, but uses different formatting (spaces in tags: < SUMMARY >).
    """

    name = "vecli_plain"
    
    # Match both <SUMMARY> and < SUMMARY > (with spaces)
    SUMMARY_PATTERN = re.compile(
        r"<\s*SUMMARY\s*>(.*?)</\s*SUMMARY\s*>",
        re.IGNORECASE | re.DOTALL
    )

    def parse(self, stdout: str, stderr: str) -> ParsedCLIResponse:
        if not stdout.strip():
            raise ParserError("vecli CLI returned empty stdout")

        content = stdout.strip()
        metadata: dict[str, Any] = {"raw_stdout": stdout}
        
        # Extract SUMMARY if present (vecli uses < SUMMARY > with spaces)
        summary_match = self.SUMMARY_PATTERN.search(content)
        if summary_match:
            summary = summary_match.group(1).strip()
            if summary:
                metadata["summary"] = summary
        
        # vecli may output warnings about non-text parts in stderr
        # Example: "there are non-text parts functionCall in the response..."
        if stderr and stderr.strip():
            stderr_clean = stderr.strip()
            metadata["stderr"] = stderr_clean
            
            # Detect if there were function calls or non-text parts
            if "non-text parts" in stderr_clean.lower():
                metadata["has_non_text_parts"] = True
            if "functionCall" in stderr_clean:
                metadata["has_function_calls"] = True
        
        return ParsedCLIResponse(content=content, metadata=metadata)
