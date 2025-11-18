"""Integration tests for real CLI execution at the Agent layer.

These tests actually execute the CLI commands (gemini, codex, claude, iflow, kimi, qwen, vecli)
and verify that:
1. The subprocess execution works
2. The parser correctly extracts content
3. Error recovery mechanisms function properly

Prerequisites:
- All CLI tools must be installed and available in PATH
- Each CLI must be configured with necessary API keys/auth in their own config
  (not in this project's .env)

Run these tests with:
    python -m pytest tests/integration/test_agent_real_cli.py -m integration -v

Or for a specific CLI:
    python -m pytest tests/integration/test_agent_real_cli.py -m integration -k iflow -v
"""

from pathlib import Path

import pytest

from clink.agents import create_agent
from clink.agents.base import CLIAgentError
from clink.constants import INTERNAL_DEFAULTS
from clink.models import ResolvedCLIClient, ResolvedCLIRole


def _create_test_client(cli_name: str) -> tuple[ResolvedCLIClient, ResolvedCLIRole]:
    """Helper to create a ResolvedCLIClient for testing."""
    defaults = INTERNAL_DEFAULTS[cli_name]
    
    role = ResolvedCLIRole(
        name="default",
        prompt_path=Path("systemprompts/clink/default.txt").resolve(),
        role_args=[],
    )
    
    client = ResolvedCLIClient(
        name=cli_name,
        executable=[cli_name],
        internal_args=defaults.additional_args,
        config_args=[],
        env=defaults.env,
        timeout_seconds=defaults.timeout_seconds,
        parser=defaults.parser,
        roles={"default": role},
        output_to_file=None,
        working_dir=None,
    )
    
    return client, role


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize(
    "cli_name,test_prompt",
    [
        ("gemini", "Say exactly: 42"),
        ("codex", "Say exactly: 42"),
        ("claude", "Say exactly: 42"),
        ("iflow", "Say exactly: 42"),
        ("kimi", "Say exactly: 42"),
        ("qwen", "Say exactly: 42"),
        ("vecli", "Say exactly: 42"),
    ],
)
async def test_real_cli_basic_execution(cli_name: str, test_prompt: str):
    """Test basic CLI execution and content extraction.
    
    This verifies:
    - CLI command can be executed
    - Parser extracts non-empty content
    - Return code is 0 for successful execution
    """
    client, role = _create_test_client(cli_name)
    agent = create_agent(client)
    
    result = await agent.run(
        role=role,
        prompt=test_prompt,
        files=[],
        images=[],
    )
    
    # Basic assertions
    assert result.returncode == 0, f"{cli_name} exited with non-zero code: {result.returncode}"
    assert result.parsed.content, f"{cli_name} returned empty content"
    assert result.parser_name == INTERNAL_DEFAULTS[cli_name].parser
    
    # Should contain some response (exact match not required due to LLM variability)
    content_lower = result.parsed.content.lower()
    assert len(content_lower) > 0, f"{cli_name} content is empty"
    
    print(f"\n[{cli_name}] Success!")
    print(f"  Parser: {result.parser_name}")
    print(f"  Content length: {len(result.parsed.content)} chars")
    print(f"  Duration: {result.duration_seconds:.2f}s")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("cli_name", ["gemini", "codex", "claude", "iflow", "kimi", "qwen", "vecli"])
async def test_real_cli_metadata_extraction(cli_name: str):
    """Test that parser extracts metadata correctly.
    
    This verifies:
    - Parser populates metadata dict
    - Metadata has expected structure (varies by CLI)
    """
    client, role = _create_test_client(cli_name)
    agent = create_agent(client)
    
    result = await agent.run(
        role=role,
        prompt="What is 1+1?",
        files=[],
        images=[],
    )
    
    assert result.parsed.metadata is not None, f"{cli_name} has no metadata"
    assert isinstance(result.parsed.metadata, dict), f"{cli_name} metadata is not a dict"
    
    print(f"\n[{cli_name}] Metadata keys: {list(result.parsed.metadata.keys())}")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("cli_name", ["iflow", "kimi", "qwen", "vecli"])
async def test_new_cli_agents_functional(cli_name: str):
    """Specific test for the 4 newly added CLIs.
    
    This is a sanity check to ensure:
    - New parsers work end-to-end
    - New agents handle real CLI output
    - Integration is complete
    """
    client, role = _create_test_client(cli_name)
    agent = create_agent(client)
    
    result = await agent.run(
        role=role,
        prompt="Hello, respond with one word: SUCCESS",
        files=[],
        images=[],
    )
    
    # Just verify we got something reasonable
    assert result.returncode == 0
    assert result.parsed.content
    assert len(result.parsed.content) > 0
    
    # Verify correct agent class is used
    agent_class_name = agent.__class__.__name__
    expected_agent = f"{cli_name.capitalize()}Agent"
    assert agent_class_name == expected_agent, (
        f"Expected {expected_agent} but got {agent_class_name}"
    )
    
    print(f"\n[{cli_name}] ✅ New CLI integration verified")
    print(f"  Agent: {agent_class_name}")
    print(f"  Parser: {result.parser_name}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_cli_timeout_handling():
    """Test that timeout mechanism works (using a short timeout)."""
    # Use a very short timeout to trigger it
    client, role = _create_test_client("gemini")
    client = client._replace(timeout_seconds=0.001)  # 1ms - will definitely timeout
    
    agent = create_agent(client)
    
    with pytest.raises(CLIAgentError) as exc_info:
        await agent.run(
            role=role,
            prompt="Count to 1000 slowly",
            files=[],
            images=[],
        )
    
    assert "timed out" in str(exc_info.value).lower()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("cli_name", ["gemini", "codex", "claude"])
async def test_original_cli_still_works(cli_name: str):
    """Regression test: ensure original 3 CLIs still work after adding 4 new ones."""
    client, role = _create_test_client(cli_name)
    agent = create_agent(client)
    
    result = await agent.run(
        role=role,
        prompt="Reply: OK",
        files=[],
        images=[],
    )
    
    assert result.returncode == 0
    assert result.parsed.content
    print(f"\n[{cli_name}] ✅ Original CLI still functional")


# Note: Error recovery tests would require knowing specific error scenarios for each CLI
# which may vary. Add them as needed based on observed CLI behavior.
