"""Tests for Kimi CLI agent."""

import asyncio
import shutil
from pathlib import Path

import pytest

from clink.agents.base import CLIAgentError
from clink.agents.kimi import KimiAgent
from clink.models import ResolvedCLIClient, ResolvedCLIRole


class DummyProcess:
    def __init__(self, *, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self, _input=None):
        return self._stdout, self._stderr


@pytest.fixture()
def kimi_agent():
    prompt_path = Path("systemprompts/clink/default.txt").resolve()
    role = ResolvedCLIRole(name="default", prompt_path=prompt_path, role_args=[])
    client = ResolvedCLIClient(
        name="kimi",
        executable=["kimi"],
        internal_args=["--yolo", "--print", "--thinking"],
        config_args=[],
        env={},
        timeout_seconds=30,
        parser="kimi_plain",
        roles={"default": role},
        output_to_file=None,
        working_dir=None,
    )
    return KimiAgent(client), role


async def _run_agent_with_process(monkeypatch, agent, role, process):
    async def fake_create_subprocess_exec(*_args, **_kwargs):
        return process

    def fake_which(executable_name):
        return f"/usr/bin/{executable_name}"

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(shutil, "which", fake_which)
    return await agent.run(role=role, prompt="do something", files=[], images=[])


@pytest.mark.asyncio
async def test_kimi_agent_recovers_from_error_with_content(monkeypatch, kimi_agent):
    """Test that kimi agent can recover if stdout contains valid content despite error code."""
    agent, role = kimi_agent
    stdout = b"TextPart(type='text', text='Partial response before error')"
    stderr = b"Warning: connection interrupted"
    process = DummyProcess(stdout=stdout, stderr=stderr, returncode=1)

    result = await _run_agent_with_process(monkeypatch, agent, role, process)

    assert result.returncode == 1
    assert "Partial response before error" in result.parsed.content


@pytest.mark.asyncio
async def test_kimi_agent_propagates_unrecoverable_error(monkeypatch, kimi_agent):
    """Test that kimi agent raises error when output is empty."""
    agent, role = kimi_agent
    stdout = b""
    stderr = b"Fatal error"
    process = DummyProcess(stdout=stdout, stderr=stderr, returncode=1)

    with pytest.raises(CLIAgentError):
        await _run_agent_with_process(monkeypatch, agent, role, process)


@pytest.mark.asyncio
async def test_kimi_agent_handles_success(monkeypatch, kimi_agent):
    """Test that kimi agent handles successful execution."""
    agent, role = kimi_agent
    stdout = b"TextPart(type='text', text='The answer is 4.')"
    process = DummyProcess(stdout=stdout, returncode=0)

    result = await _run_agent_with_process(monkeypatch, agent, role, process)

    assert result.returncode == 0
    assert "The answer is 4." in result.parsed.content
