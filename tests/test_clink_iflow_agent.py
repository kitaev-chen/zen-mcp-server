"""Tests for iflow CLI agent."""

import asyncio
import shutil
from pathlib import Path

import pytest

from clink.agents.base import CLIAgentError
from clink.agents.iflow import IflowAgent
from clink.models import ResolvedCLIClient, ResolvedCLIRole


class DummyProcess:
    def __init__(self, *, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self, _input=None):
        return self._stdout, self._stderr


@pytest.fixture()
def iflow_agent():
    prompt_path = Path("systemprompts/clink/default.txt").resolve()
    role = ResolvedCLIRole(name="default", prompt_path=prompt_path, role_args=[])
    client = ResolvedCLIClient(
        name="iflow",
        executable=["iflow"],
        internal_args=[],
        config_args=[],
        env={},
        timeout_seconds=30,
        parser="iflow_plain",
        roles={"default": role},
        output_to_file=None,
        working_dir=None,
    )
    return IflowAgent(client), role


async def _run_agent_with_process(monkeypatch, agent, role, process):
    async def fake_create_subprocess_exec(*_args, **_kwargs):
        return process

    def fake_which(executable_name):
        return f"/usr/bin/{executable_name}"

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(shutil, "which", fake_which)
    return await agent.run(role=role, prompt="do something", files=[], images=[])


@pytest.mark.asyncio
async def test_iflow_agent_recovers_from_error_with_content(monkeypatch, iflow_agent):
    """Test that iflow agent can recover if stdout contains valid content despite error code."""
    agent, role = iflow_agent
    stdout = b"""Response content here

<Execution Info>
{
  "session-id": "test-session",
  "assistantRounds": 1,
  "executionTimeMs": 5000,
  "tokenUsage": {"input": 100, "output": 20}
}
</Execution Info>"""
    stderr = b"Warning: some non-fatal error"
    process = DummyProcess(stdout=stdout, stderr=stderr, returncode=1)

    result = await _run_agent_with_process(monkeypatch, agent, role, process)

    assert result.returncode == 1
    assert "Response content here" in result.parsed.content
    assert result.parsed.metadata.get("execution_info") is not None


@pytest.mark.asyncio
async def test_iflow_agent_propagates_unrecoverable_error(monkeypatch, iflow_agent):
    """Test that iflow agent raises error when no valid content is found."""
    agent, role = iflow_agent
    stdout = b""
    stderr = b"Fatal error: cannot start"
    process = DummyProcess(stdout=stdout, stderr=stderr, returncode=1)

    with pytest.raises(CLIAgentError):
        await _run_agent_with_process(monkeypatch, agent, role, process)


@pytest.mark.asyncio
async def test_iflow_agent_handles_success(monkeypatch, iflow_agent):
    """Test that iflow agent handles successful execution."""
    agent, role = iflow_agent
    stdout = b"The answer is 42."
    process = DummyProcess(stdout=stdout, returncode=0)

    result = await _run_agent_with_process(monkeypatch, agent, role, process)

    assert result.returncode == 0
    assert "The answer is 42." in result.parsed.content
