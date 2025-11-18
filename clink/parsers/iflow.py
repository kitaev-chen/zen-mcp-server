"""Parser for iflow CLI plain text output."""

from __future__ import annotations

from typing import Any

from .base import BaseParser, ParsedCLIResponse, ParserError


class IflowPlainParser(BaseParser):
    """Parse plain text stdout produced by iflow CLI.
    
    iflow does not support JSON output format natively. It outputs the response
    in plain text to stdout, with execution metadata at the bottom.
    """

    name = "iflow_plain"

    def parse(self, stdout: str, stderr: str) -> ParsedCLIResponse:
        if not stdout.strip():
            raise ParserError("iflow CLI returned empty stdout")

        lines = stdout.strip().splitlines()
        
        # Find the <Execution Info> section
        execution_info_start = -1
        for i, line in enumerate(lines):
            if "<Execution Info>" in line:
                execution_info_start = i
                break
        
        # Extract content (everything before <Execution Info>)
        if execution_info_start >= 0:
            content_lines = lines[:execution_info_start]
        else:
            # No execution info found, use all lines
            content_lines = lines
        
        # Remove empty lines from the end
        while content_lines and not content_lines[-1].strip():
            content_lines.pop()
        
        content = "\n".join(content_lines).strip()
        
        if not content:
            raise ParserError("iflow CLI returned no content before execution info")
        
        metadata: dict[str, Any] = {"raw_stdout": stdout}
        
        # Try to extract execution info if present
        if execution_info_start >= 0 and execution_info_start + 1 < len(lines):
            # The execution info is between <Execution Info> and </Execution Info>
            try:
                import json
                info_lines = []
                for i in range(execution_info_start + 1, len(lines)):
                    if "</Execution Info>" in lines[i]:
                        break
                    info_lines.append(lines[i])
                
                if info_lines:
                    info_json = "\n".join(info_lines)
                    execution_info = json.loads(info_json)
                    metadata["execution_info"] = execution_info
                    
                    # Extract token usage if available
                    if "tokenUsage" in execution_info:
                        metadata["usage"] = execution_info["tokenUsage"]
            except json.JSONDecodeError:
                # If we can't parse the execution info, just skip it
                pass
        
        if stderr and stderr.strip():
            stderr_clean = stderr.strip()
            # Filter out known Windows compatibility warnings that don't affect functionality
            if not any(harmless in stderr_clean for harmless in [
                "The system cannot find the path specified",  # iflow Windows path warning
            ]):
                metadata["stderr"] = stderr_clean
        
        return ParsedCLIResponse(content=content, metadata=metadata)
