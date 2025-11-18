"""Tests for Qwen CLI agent."""

import asyncio
import shutil
from pathlib import Path

import pytest

from clink.agents.base import CLIAgentError
from clink.agents.qwen import QwenAgent
from clink.models import ResolvedCLIClient, ResolvedCLIRole


class DummyProcess:
    def __init__(self, *, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self, _input=None):
        return self._stdout, self._stderr


@pytest.fixture()
def qwen_agent():
    prompt_path = Path("systemprompts/clink/default.txt").resolve()
    role = ResolvedCLIRole(name="default", prompt_path=prompt_path, role_args=[])
    client = ResolvedCLIClient(
        name="qwen",
        executable=["qwen"],
        internal_args=["-o", "json"],
        config_args=[],
        env={},
        timeout_seconds=30,
        parser="gemini_json",
        roles={"default": role},
        output_to_file=None,
        working_dir=None,
    )
    return QwenAgent(client), role


async def _run_agent_with_process(monkeypatch, agent, role, process):
    async def fake_create_subprocess_exec(*_args, **_kwargs):
        return process

    def fake_which(executable_name):
        return f"/usr/bin/{executable_name}"

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(shutil, "which", fake_which)
    return await agent.run(role=role, prompt="do something", files=[], images=[])


@pytest.mark.asyncio
async def test_qwen_agent_recovers_tool_error(monkeypatch, qwen_agent):
    """Test that qwen agent recovers from tool execution errors like Gemini."""
    agent, role = qwen_agent
    error_json = """{
  "error": {
    "type": "ToolExecutionError",
    "message": "Failed to execute edit tool: file not found",
    "code": "file_not_found"
  }
}"""
    stderr = ("Error: File not found.\n" + error_json).encode()
    process = DummyProcess(stderr=stderr, returncode=1)

    result = await _run_agent_with_process(monkeypatch, agent, role, process)

    assert result.returncode == 1
    assert result.parsed.metadata["cli_error_recovered"] is True
    assert result.parsed.metadata["cli_error_code"] == "file_not_found"
    assert "Qwen CLI reported a tool failure" in result.parsed.content


@pytest.mark.asyncio
async def test_qwen_agent_propagates_unrecoverable_error(monkeypatch, qwen_agent):
    """Test that qwen agent raises error when no structured payload exists."""
    agent, role = qwen_agent
    stderr = b"Plain error without JSON structure"
    process = DummyProcess(stderr=stderr, returncode=1)

    with pytest.raises(CLIAgentError):
        await _run_agent_with_process(monkeypatch, agent, role, process)


@pytest.mark.asyncio
async def test_qwen_agent_handles_success(monkeypatch, qwen_agent):
    """Test that qwen agent handles successful execution."""
    agent, role = qwen_agent
    stdout = b'{"response": "The answer is 4.", "stats": {"models": {}}}'
    process = DummyProcess(stdout=stdout, returncode=0)

    result = await _run_agent_with_process(monkeypatch, agent, role, process)

    assert result.returncode == 0
    assert "The answer is 4." in result.parsed.content


@pytest.mark.asyncio
async def test_qwen_agent_recovers_from_windows_crash(monkeypatch, qwen_agent):
    """Test that qwen agent recovers from Windows libuv crash (exit code 3221226505)."""
    agent, role = qwen_agent
    # Simulate Windows crash: valid JSON output but abnormal exit code
    stdout = b'{"response": "Hello! I am ready to assist.", "stats": {"models": {}}}'
    stderr = b"Assertion failed: !(handle->flags & UV_HANDLE_CLOSING), file c:\\ws\\deps\\uv\\src\\win\\async.c, line 76"
    process = DummyProcess(stdout=stdout, stderr=stderr, returncode=3221226505)

    result = await _run_agent_with_process(monkeypatch, agent, role, process)

    # Should recover and return the valid response
    assert result.returncode == 3221226505  # Preserves original error code
    assert "Hello! I am ready to assist." in result.parsed.content
