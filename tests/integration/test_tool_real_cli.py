"""Integration tests for real CLI execution at the Tool layer (CLinkTool).

These tests verify the complete end-to-end flow:
    MCP Tool API → Registry → ResolvedCLIClient → Agent → Subprocess → Parser → Response

This layer tests:
1. Configuration loading from conf/cli_clients/*.json
2. Registry client resolution
3. CLinkTool parameter handling
4. Response formatting for MCP
5. Metadata propagation

Prerequisites:
- All CLI tools must be installed and available in PATH
- Each CLI must be configured with necessary API keys/auth in their own config
- Configuration files must exist in conf/cli_clients/

Run these tests with:
    python -m pytest tests/integration/test_tool_real_cli.py -m integration -v
"""

import json

import pytest

from tools.clink import CLinkTool


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize(
    "cli_name",
    ["gemini", "codex", "claude", "iflow", "kimi", "qwen", "vecli"],
)
async def test_clink_tool_real_cli_execution(cli_name: str):
    """Test CLinkTool with real CLI execution.
    
    This verifies the complete MCP tool flow:
    - Tool receives MCP-formatted arguments
    - Registry resolves CLI configuration
    - Agent executes real CLI
    - Parser extracts content
    - Tool formats response for MCP
    """
    tool = CLinkTool()
    
    arguments = {
        "prompt": "Say exactly: INTEGRATION_TEST",
        "cli_name": cli_name,
        "role": "default",
        "absolute_file_paths": [],
        "images": [],
    }
    
    results = await tool.execute(arguments)
    
    # Verify result structure
    assert results, f"No results returned for {cli_name}"
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    
    result = results[0]
    payload = json.loads(result.text)
    
    # Verify response structure
    assert "status" in payload, f"{cli_name}: Missing 'status' in response"
    assert "content" in payload, f"{cli_name}: Missing 'content' in response"
    assert "metadata" in payload, f"{cli_name}: Missing 'metadata' in response"
    
    # Verify status is success
    assert payload["status"] in {"success", "continuation_available"}, (
        f"{cli_name}: Unexpected status: {payload['status']}"
    )
    
    # Verify content is non-empty
    assert payload["content"], f"{cli_name}: Content is empty"
    assert len(payload["content"]) > 0
    
    # Verify metadata
    metadata = payload["metadata"]
    assert metadata["cli_name"] == cli_name
    assert "command" in metadata
    assert "parser_name" in metadata
    assert "duration_seconds" in metadata
    
    print(f"\n[{cli_name}] CLinkTool Integration Test ✅")
    print(f"  Status: {payload['status']}")
    print(f"  Content length: {len(payload['content'])} chars")
    print(f"  Parser: {metadata['parser_name']}")
    print(f"  Duration: {metadata['duration_seconds']:.2f}s")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("cli_name", ["iflow", "kimi", "qwen", "vecli"])
async def test_new_cli_tool_integration(cli_name: str):
    """Specific test for newly added CLIs at the Tool layer.
    
    Verifies:
    - Configuration files are loaded correctly
    - Registry resolves new CLI clients
    - Complete tool chain works
    """
    tool = CLinkTool()
    
    arguments = {
        "prompt": "Respond with: NEW_CLI_OK",
        "cli_name": cli_name,
        "role": "default",
        "absolute_file_paths": [],
        "images": [],
    }
    
    results = await tool.execute(arguments)
    payload = json.loads(results[0].text)
    
    assert payload["status"] == "success"
    assert payload["metadata"]["cli_name"] == cli_name
    
    # Verify correct parser is used
    from clink.constants import INTERNAL_DEFAULTS
    expected_parser = INTERNAL_DEFAULTS[cli_name].parser
    assert payload["metadata"]["parser_name"] == expected_parser
    
    print(f"\n[{cli_name}] ✅ New CLI fully integrated into CLinkTool")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_tool_defaults_to_first_cli():
    """Test that CLinkTool uses default CLI when none specified."""
    tool = CLinkTool()
    
    arguments = {
        "prompt": "Say: DEFAULT_CLI_TEST",
        "absolute_file_paths": [],
        "images": [],
        # Note: cli_name is intentionally omitted
    }
    
    results = await tool.execute(arguments)
    payload = json.loads(results[0].text)
    
    assert payload["status"] == "success"
    assert "cli_name" in payload["metadata"]
    
    default_cli = payload["metadata"]["cli_name"]
    print(f"\n✅ Tool defaulted to: {default_cli}")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("cli_name", ["gemini", "codex", "claude"])
async def test_original_cli_tool_integration(cli_name: str):
    """Regression test: ensure original CLIs work through Tool layer."""
    tool = CLinkTool()
    
    arguments = {
        "prompt": "Reply: ORIGINAL_CLI_OK",
        "cli_name": cli_name,
        "role": "default",
        "absolute_file_paths": [],
        "images": [],
    }
    
    results = await tool.execute(arguments)
    payload = json.loads(results[0].text)
    
    assert payload["status"] == "success"
    assert payload["metadata"]["cli_name"] == cli_name
    
    print(f"\n[{cli_name}] ✅ Original CLI still works through Tool layer")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_tool_with_different_roles():
    """Test that different roles can be used (using a CLI that supports roles)."""
    tool = CLinkTool()
    
    # Test with 'planner' role (defined in conf/cli_clients/*.json)
    arguments = {
        "prompt": "Create a plan",
        "cli_name": "gemini",  # or any CLI with 'planner' role defined
        "role": "planner",
        "absolute_file_paths": [],
        "images": [],
    }
    
    results = await tool.execute(arguments)
    payload = json.loads(results[0].text)
    
    assert payload["status"] == "success"
    print(f"\n✅ Tool works with 'planner' role")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_tool_response_truncation_with_real_cli():
    """Test that very long CLI output is handled correctly by the tool.
    
    Note: This test may be slow if the CLI actually generates a lot of content.
    """
    tool = CLinkTool()
    
    # Ask for a long response
    arguments = {
        "prompt": "List numbers from 1 to 100",
        "cli_name": "gemini",
        "role": "default",
        "absolute_file_paths": [],
        "images": [],
    }
    
    results = await tool.execute(arguments)
    payload = json.loads(results[0].text)
    
    # Should still succeed even if truncated
    assert payload["status"] in {"success", "continuation_available"}
    
    # Check if truncation metadata is present if output was large
    if "output_truncated" in payload["metadata"]:
        print(f"\n✅ Tool handled large output with truncation")
    else:
        print(f"\n✅ Tool handled output (not truncated)")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_all_cli_configs_loadable():
    """Smoke test: ensure all 7 CLIs can be loaded from registry."""
    from clink import get_registry
    
    registry = get_registry()
    clients = registry.list_clients()
    
    expected_clis = {"gemini", "codex", "claude", "iflow", "kimi", "qwen", "vecli"}
    
    # All 7 should be present
    assert expected_clis.issubset(set(clients)), (
        f"Missing CLIs. Expected: {expected_clis}, Got: {set(clients)}"
    )
    
    print(f"\n✅ All 7 CLIs loaded from registry: {clients}")
    
    # Verify each has a default role
    for cli_name in expected_clis:
        roles = registry.list_roles(cli_name)
        assert "default" in roles, f"{cli_name} missing 'default' role"
        print(f"  {cli_name}: roles = {roles}")
