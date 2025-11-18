"""Tests for vecli CLI agent."""

import asyncio
import shutil
from pathlib import Path

import pytest

from clink.agents.base import CLIAgentError
from clink.agents.vecli import VecliAgent
from clink.models import ResolvedCLIClient, ResolvedCLIRole


class DummyProcess:
    def __init__(self, *, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self, _input):
        return self._stdout, self._stderr


@pytest.fixture()
def vecli_agent():
    prompt_path = Path("systemprompts/clink/default.txt").resolve()
    role = ResolvedCLIRole(name="default", prompt_path=prompt_path, role_args=[])
    client = ResolvedCLIClient(
        name="vecli",
        executable=["vecli"],
        internal_args=[],
        config_args=[],
        env={},
        timeout_seconds=30,
        parser="vecli_plain",
        roles={"default": role},
        output_to_file=None,
        working_dir=None,
    )
    return VecliAgent(client), role


async def _run_agent_with_process(monkeypatch, agent, role, process):
    async def fake_create_subprocess_exec(*_args, **_kwargs):
        return process

    def fake_which(executable_name):
        return f"/usr/bin/{executable_name}"

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(shutil, "which", fake_which)
    return await agent.run(role=role, prompt="do something", files=[], images=[])


@pytest.mark.asyncio
async def test_vecli_agent_recovers_from_error_with_content(monkeypatch, vecli_agent):
    """Test that vecli agent can recover if stdout contains valid content despite error code."""
    agent, role = vecli_agent
    stdout = b"Partial response from vecli.\n\n< SUMMARY >\nPartial response delivered.\n</SUMMARY >"
    stderr = b"Warning: request throttled"
    process = DummyProcess(stdout=stdout, stderr=stderr, returncode=1)

    result = await _run_agent_with_process(monkeypatch, agent, role, process)

    assert result.returncode == 1
    assert "Partial response" in result.parsed.content


@pytest.mark.asyncio
async def test_vecli_agent_propagates_unrecoverable_error(monkeypatch, vecli_agent):
    """Test that vecli agent raises error when no valid content is found."""
    agent, role = vecli_agent
    stdout = b""
    stderr = b"Fatal error"
    process = DummyProcess(stdout=stdout, stderr=stderr, returncode=1)

    with pytest.raises(CLIAgentError):
        await _run_agent_with_process(monkeypatch, agent, role, process)


@pytest.mark.asyncio
async def test_vecli_agent_handles_success(monkeypatch, vecli_agent):
    """Test that vecli agent handles successful execution."""
    agent, role = vecli_agent
    stdout = b"The answer is 4.\n\n< SUMMARY >\nProvided answer to math question.\n</SUMMARY >"
    process = DummyProcess(stdout=stdout, returncode=0)

    result = await _run_agent_with_process(monkeypatch, agent, role, process)

    assert result.returncode == 0
    assert "The answer is 4." in result.parsed.content
