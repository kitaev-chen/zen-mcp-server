"""iflow-specific CLI agent hooks."""

from __future__ import annotations

import asyncio
import re
import shutil
import time
from collections.abc import Sequence
from typing import Any

from clink.models import ResolvedCLIClient, ResolvedCLIRole
from clink.parsers.base import ParserError

from .base import AgentOutput, BaseCLIAgent, CLIAgentError, DEFAULT_STREAM_LIMIT

class IflowAgent(BaseCLIAgent):
    """iflow CLI agent with plain text parsing support.
    
    iflow requires the prompt to be passed via --prompt argument,
    not via stdin like other CLIs.
    """

    def __init__(self, client: ResolvedCLIClient):
        super().__init__(client)
    
    async def run(
        self,
        *,
        role: ResolvedCLIRole,
        prompt: str,
        system_prompt: str | None = None,
        files: Sequence[str],
        images: Sequence[str],
    ) -> AgentOutput:
        """Override run with multi-round support for generic responses.
        
        iflow often returns a generic 'ready to help' response on first call.
        When detected (via parser metadata), we extract session-id and make
        a follow-up call with "继续" to get the actual response.
        """
        _ = (files, images, system_prompt)  # Unused for iflow
        
        # First round: normal call
        result = await self._run_single_call(role=role, prompt=prompt)
        
        # Check parser's response type classification
        response_type = result.parsed.metadata.get("response_type")
        detected_pattern = result.parsed.metadata.get("detected_pattern", "unknown")
        
        # Decide if retry is needed based on response type and prompt complexity
        should_retry = self._should_retry(response_type, prompt)
        
        if should_retry:
            session_id = self._extract_session_id(result.stdout, result.parsed.metadata)
            
            if session_id:
                self._logger.info(
                    f"iflow returned {response_type} response (pattern: '{detected_pattern}'), "
                    f"attempting follow-up with session {session_id[:40]}..."
                )
                
                # Second round: resume session with "继续" to get actual response
                try:
                    follow_up = await self._run_with_session(
                        role=role,
                        session_id=session_id,
                    )
                    
                    # Only use follow-up if it doesn't need retry too
                    follow_up_type = follow_up.parsed.metadata.get("response_type")
                    if follow_up and not self._should_retry(follow_up_type, prompt):
                        self._logger.info("iflow follow-up call returned actual response")
                        return follow_up
                    else:
                        self._logger.warning(f"iflow follow-up also returned {follow_up_type} response")
                except Exception as e:
                    self._logger.warning(f"iflow follow-up call failed: {e}")
            else:
                self._logger.warning(f"iflow returned {response_type} response but no session-id found")
        
        return result

    def _should_retry(self, response_type: str | None, prompt: str) -> bool:
        """Determine if a retry is needed based on response type and prompt complexity.
        
        Args:
            response_type: Type from parser ("generic", "clarification", "contextual", or None)
            prompt: The original user prompt
            
        Returns:
            True if retry should be attempted
        """
        if not response_type:
            # No problematic patterns detected
            return False
        
        if response_type == "generic":
            # TRUE_GENERIC_PATTERNS - always retry
            return True
        
        if response_type in ("clarification", "contextual"):
            # May be valid for simple prompts, check prompt complexity
            if self._is_complex_task(prompt):
                # Complex task + clarification/contextual = needs retry
                return True
            else:
                # Simple prompt + clarification/contextual = acceptable
                self._logger.debug(f"Accepting {response_type} response for simple prompt")
                return False
        
        return False

    def _is_complex_task(self, prompt: str) -> bool:
        """Determine if the prompt represents a complex task.
        
        Complex tasks should not result in clarification requests.
        Simple prompts (hello, test, hi) may legitimately trigger clarifications.
        """
        # Word count heuristic
        words = prompt.split()
        if len(words) <= 5:
            return False
        
        # Task keywords that indicate complex work is expected
        complex_keywords = [
            # English
            "analyze", "write", "debug", "fix", "refactor", "implement",
            "optimize", "review", "create", "build", "design", "explain",
            "compare", "evaluate", "generate", "modify", "update",
            # Chinese
            "分析", "编写", "调试", "修复", "重构", "实现",
            "优化", "审查", "创建", "构建", "设计", "解释",
            "比较", "评估", "生成", "修改", "更新",
        ]
        
        prompt_lower = prompt.lower()
        has_complex_keyword = any(kw in prompt_lower for kw in complex_keywords)
        
        # Complex if: has task keywords OR long prompt (>50 chars with >10 words)
        if has_complex_keyword:
            return True
        if len(prompt) > 50 and len(words) > 10:
            return True
        
        return False

    async def _run_single_call(
        self,
        *,
        role: ResolvedCLIRole,
        prompt: str,
        extra_args: list[str] | None = None,
    ) -> AgentOutput:
        """Execute a single iflow CLI call."""
        # Build base command
        command = self._build_command(role=role, system_prompt=None)
        
        # Add prompt via --prompt argument
        command.extend(["--prompt", prompt])
        
        # Add any extra arguments (e.g., --resume)
        if extra_args:
            command.extend(extra_args)
        
        env = self._build_environment()

        # Resolve executable
        executable_name = command[0]
        resolved_executable = shutil.which(executable_name)
        if resolved_executable is None:
            raise CLIAgentError(
                f"Executable '{executable_name}' not found in PATH for CLI '{self.client.name}'. "
                f"Ensure the command is installed and accessible."
            )
        command[0] = resolved_executable

        sanitized_command = list(command)
        cwd = str(self.client.working_dir) if self.client.working_dir else None
        start_time = time.monotonic()

        self._logger.debug("Executing CLI command: %s", " ".join(sanitized_command))

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.DEVNULL,  # iflow doesn't use stdin
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                limit=DEFAULT_STREAM_LIMIT,
                env=env,
            )
        except FileNotFoundError as exc:
            raise CLIAgentError(f"Executable not found for CLI '{self.client.name}': {exc}") from exc

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=self.client.timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.communicate()
            raise CLIAgentError(
                f"CLI '{self.client.name}' timed out after {self.client.timeout_seconds} seconds",
                returncode=None,
            ) from exc

        duration = time.monotonic() - start_time
        return_code = process.returncode
        stdout_text = stdout_bytes.decode("utf-8", errors="replace")
        stderr_text = stderr_bytes.decode("utf-8", errors="replace")

        if return_code != 0:
            recovered = self._recover_from_error(
                returncode=return_code,
                stdout=stdout_text,
                stderr=stderr_text,
                sanitized_command=sanitized_command,
                duration_seconds=duration,
                output_file_content=None,
            )
            if recovered is not None:
                return recovered

        if return_code != 0:
            raise CLIAgentError(
                f"CLI '{self.client.name}' exited with status {return_code}",
                returncode=return_code,
                stdout=stdout_text,
                stderr=stderr_text,
            )

        try:
            parsed = self._parser.parse(stdout_text, stderr_text)
        except ParserError as exc:
            raise CLIAgentError(
                f"Failed to parse output from CLI '{self.client.name}': {exc}",
                returncode=return_code,
                stdout=stdout_text,
                stderr=stderr_text,
            ) from exc

        return AgentOutput(
            parsed=parsed,
            sanitized_command=sanitized_command,
            returncode=return_code,
            stdout=stdout_text,
            stderr=stderr_text,
            duration_seconds=duration,
            parser_name=self._parser.name,
            output_file_content=None,
        )

    def _recover_from_error(
        self,
        *,
        returncode: int,
        stdout: str,
        stderr: str,
        sanitized_command: list[str],
        duration_seconds: float,
        output_file_content: str | None,
    ) -> AgentOutput | None:
        """iflow may still output useful content even with non-zero exit codes.
        
        Try to parse stdout/stderr to extract any partial response.
        """
        try:
            parsed = self._parser.parse(stdout, stderr)
        except ParserError:
            return None

        return AgentOutput(
            parsed=parsed,
            sanitized_command=sanitized_command,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration_seconds,
            parser_name=self._parser.name,
            output_file_content=output_file_content,
        )

    def _extract_session_id(self, stdout: str, metadata: dict[str, Any]) -> str | None:
        """Extract session-id from iflow output.
        
        iflow outputs execution info with session-id that can be used to resume.
        """
        # Method 1: From parsed metadata (execution_info)
        exec_info = metadata.get("execution_info", {})
        if isinstance(exec_info, dict):
            # Try common key variations
            for key in ["session-id", "session_id", "sessionId"]:
                if key in exec_info:
                    return exec_info[key]
        
        # Method 2: Regex from raw stdout
        # Pattern: "session-id": "session-xxx" or session_id: xxx
        patterns = [
            r'"session-id"\s*:\s*"([^"]+)"',
            r'"session_id"\s*:\s*"([^"]+)"',
            r'"sessionId"\s*:\s*"([^"]+)"',
            r'session[_-]?id["\']?\s*[:=]\s*["\']?([^"\',\s\}]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, stdout, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    async def _run_with_session(
        self,
        *,
        role: ResolvedCLIRole,
        session_id: str,
    ) -> AgentOutput:
        """Make a follow-up call using session resumption.
        
        Uses --resume to continue the conversation and get actual response.
        The simple "继续" prompt tells iflow to proceed with the task.
        """
        # Simple continue prompt - iflow already has context from first call
        follow_up_prompt = "继续"
        
        # Use --resume with session-id to continue conversation
        return await self._run_single_call(
            role=role,
            prompt=follow_up_prompt,
            extra_args=["--resume", session_id],
        )
