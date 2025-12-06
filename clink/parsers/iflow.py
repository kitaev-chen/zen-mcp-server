"""Parser for iflow CLI plain text output."""

from __future__ import annotations

import re
from typing import Any

from .base import BaseParser, ParsedCLIResponse, ParserError


# Patterns split into two categories:
# 1. CLARIFICATION_PATTERNS - may be valid for simple prompts
# 2. TRUE_GENERIC_PATTERNS - always indicate no actual work was done

CLARIFICATION_PATTERNS = [
    "Could you please clarify",
    "please clarify what task",
    "What would you like",
    "How can I help you",
    "What can I help",
    "I don't see a specific task",
    "有什么我可以帮助",
    "有什么可以帮",
]

TRUE_GENERIC_PATTERNS = [
    "Ready to assist",
    "好的，我明白了",
    "setting up the context",
    "setting up context",
]

# Patterns that suggest content is contextual awareness, not actual analysis
# These alone don't mean invalid, but combined with short length may indicate no work done
CONTEXT_AWARENESS_PATTERNS = [
    "I can see this is",
    "I understand the setup",
    "I can see you have",
    "Looking at the project",
]


class IflowPlainParser(BaseParser):
    """Parse plain text stdout produced by iflow CLI.
    
    iflow does not support JSON output format natively. It outputs the response
    in plain text to stdout, with execution metadata at the bottom.
    
    This parser also:
    - Removes <think>...</think> blocks (internal reasoning)
    - Detects response types with context-aware logic for agent decision
    """

    name = "iflow_plain"

    def _has_substantial_content(self, content: str) -> bool:
        """Check if response contains substantial analysis beyond patterns."""
        # Indicators of actual work being done
        work_indicators = [
            # Code/technical
            "```", "def ", "class ", "import ", "function",
            # Analysis keywords
            "analysis", "recommendation", "suggestion", "conclusion",
            "issue", "problem", "solution", "fix", "error",
            "建议", "分析", "结论", "方案", "优化", "问题", "修复",
            # List/structure indicators
            "1.", "2.", "3.", "- ", "* ",
        ]
        
        content_lower = content.lower()
        indicator_count = sum(1 for ind in work_indicators if ind.lower() in content_lower)
        
        # If has multiple work indicators or long content, it's substantial
        if indicator_count >= 3:
            return True
        if len(content) > 500 and indicator_count >= 1:
            return True
        
        return False

    def _detect_response_type(self, content: str) -> tuple[str | None, str | None]:
        """Detect response type and triggering pattern.
        
        Returns:
            (response_type, detected_pattern) where response_type is:
            - "generic": truly no work done, should retry
            - "clarification": asking for clarification, may be valid for simple prompts
            - "contextual": showing context awareness, valid if has substantial content
            - None: normal response
        """
        content_lower = content.lower()
        
        # Check TRUE_GENERIC_PATTERNS first - these are always problematic
        for pattern in TRUE_GENERIC_PATTERNS:
            if pattern.lower() in content_lower:
                return "generic", pattern
        
        # Check CONTEXT_AWARENESS_PATTERNS - valid if has substantial content
        for pattern in CONTEXT_AWARENESS_PATTERNS:
            if pattern.lower() in content_lower:
                if self._has_substantial_content(content):
                    return None, None  # Valid response with context awareness
                else:
                    return "contextual", pattern
        
        # Check CLARIFICATION_PATTERNS - may be valid for simple prompts
        for pattern in CLARIFICATION_PATTERNS:
            if pattern.lower() in content_lower:
                if self._has_substantial_content(content):
                    return None, None  # Valid: clarification + substantial content
                else:
                    return "clarification", pattern
        
        return None, None

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

        # Filter out known Windows system error messages from stdout
        # These can appear at the beginning of iflow output on Windows
        windows_noise_patterns = [
            "The system cannot find the path specified",
            "The system cannot find the file specified",
        ]
        for pattern in windows_noise_patterns:
            if content.startswith(pattern):
                # Remove the error line from the beginning
                split_lines = content.split("\n", 1)
                content = split_lines[1].strip() if len(split_lines) > 1 else ""
        
        # Remove <think>...</think> blocks (iFlow's internal reasoning)
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        
        if not content:
            raise ParserError("iflow CLI returned no content before execution info")
        
        metadata: dict[str, Any] = {"raw_stdout": stdout}
        
        # Context-aware response type detection
        # Only check short responses - long responses are likely valid
        if len(content) < 800:
            response_type, detected_pattern = self._detect_response_type(content)
            if response_type:
                metadata["response_type"] = response_type
                metadata["detected_pattern"] = detected_pattern
        
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
