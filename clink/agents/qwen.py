"""Qwen-specific CLI agent hooks."""

from __future__ import annotations

import asyncio
import json
import shutil
import time
from collections.abc import Sequence
from typing import Any

from clink.models import ResolvedCLIClient, ResolvedCLIRole
from clink.parsers.base import ParsedCLIResponse, ParserError

from .base import AgentOutput, BaseCLIAgent, CLIAgentError, DEFAULT_STREAM_LIMIT


class QwenAgent(BaseCLIAgent):
    """Qwen CLI agent with error recovery similar to Gemini.
    
    Qwen uses the same JSON output format as Gemini, and requires
    the prompt to be passed via --prompt argument, not via stdin.
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
        """Override run to pass prompt via --prompt argument instead of stdin."""
        _ = (files, images, system_prompt)  # Unused for qwen
        
        # Build base command
        command = self._build_command(role=role, system_prompt=None)
        
        # Add prompt via --prompt argument
        command.extend(["--prompt", prompt])
        
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
                stdin=asyncio.subprocess.DEVNULL,  # qwen doesn't use stdin
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
        """Recover from Qwen CLI errors.
        
        Qwen on Windows may crash (libuv error) after successfully outputting JSON.
        First try to parse stdout as valid response, then handle error payloads.
        """
        # Try to parse stdout as a valid response first
        # This handles Windows crashes where JSON is output but process crashes
        if stdout and stdout.strip():
            try:
                parsed = self._parser.parse(stdout, stderr)
                self._logger.warning(
                    f"CLI '{self.client.name}' exited with code {returncode} but produced valid output. "
                    f"This may indicate a Windows compatibility issue (libuv crash)."
                )
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
            except ParserError:
                # If parsing fails, try error payload recovery below
                pass
        
        # Try to extract error payload from stderr/stdout
        combined = "\n".join(part for part in (stderr, stdout) if part)
        if not combined:
            return None

        brace_index = combined.find("{")
        if brace_index == -1:
            return None

        json_candidate = combined[brace_index:]
        try:
            payload: dict[str, Any] = json.loads(json_candidate)
        except json.JSONDecodeError:
            return None

        error_block = payload.get("error")
        if not isinstance(error_block, dict):
            return None

        code = error_block.get("code")
        err_type = error_block.get("type")
        detail_message = error_block.get("message")

        prologue = combined[:brace_index].strip()
        lines: list[str] = []
        if prologue and (not detail_message or prologue not in detail_message):
            lines.append(prologue)
        if detail_message:
            lines.append(detail_message)

        header = "Qwen CLI reported a tool failure"
        if code:
            header = f"{header} ({code})"
        elif err_type:
            header = f"{header} ({err_type})"

        content_lines = [header.rstrip(".") + ".", *lines]
        message = "\n".join(content_lines).strip()

        metadata = {
            "cli_error_recovered": True,
            "cli_error_code": code,
            "cli_error_type": err_type,
            "cli_error_payload": payload,
        }

        parsed = ParsedCLIResponse(content=message or header, metadata=metadata)
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
