"""Tests for CLI Provider functionality."""

from unittest.mock import MagicMock, patch

import pytest

from providers.cli import CLIModelProvider
from providers.registries.cli import CLIModelRegistry
from providers.shared import ProviderType


class TestCLIModelRegistry:
    """Test CLIModelRegistry class functionality."""

    def test_registry_loads_models(self):
        """Test CLIModelRegistry loads models from cli_models.json."""
        registry = CLIModelRegistry()

        # Should have models loaded
        models = registry.list_models()
        assert len(models) > 0

        # Check for expected CLI models
        assert "cli:gemini" in models
        assert "cli:kimi" in models
        assert "cli:qwen" in models

    def test_registry_resolves_aliases(self):
        """Test CLIModelRegistry resolves aliases correctly."""
        registry = CLIModelRegistry()

        # Test alias resolution
        cap = registry.resolve("gemini cli")
        assert cap is not None
        assert cap.model_name == "cli:gemini"

        cap = registry.resolve("kimi-cli")
        assert cap is not None
        assert cap.model_name == "cli:kimi"

    def test_registry_provider_type(self):
        """Test CLIModelRegistry returns correct provider type."""
        registry = CLIModelRegistry()

        cap = registry.resolve("cli:gemini")
        assert cap is not None
        assert cap.provider == ProviderType.CLI

    def test_cli_models_no_extended_thinking(self):
        """Test CLI models don't claim extended thinking support."""
        registry = CLIModelRegistry()

        for model_name in registry.list_models():
            cap = registry.get_model_config(model_name)
            assert cap is not None
            # CLI models should NOT claim API-level extended thinking
            assert cap.supports_extended_thinking is False, f"{model_name} should not support extended_thinking"


class TestCLIModelProvider:
    """Test CLIModelProvider class functionality."""

    def test_provider_initialization(self):
        """Test CLIModelProvider initializes correctly."""
        provider = CLIModelProvider()

        assert provider.get_provider_type() == ProviderType.CLI
        # CLI provider doesn't need a real API key
        assert provider.api_key is not None

    def test_provider_has_model_capabilities(self):
        """Test CLIModelProvider has MODEL_CAPABILITIES populated."""
        provider = CLIModelProvider()

        caps = provider.get_all_model_capabilities()
        assert len(caps) > 0

        # Should include CLI models
        assert "cli:gemini" in caps
        assert "cli:kimi" in caps

    def test_get_cli_client_name(self):
        """Test _get_cli_client_name extracts client name correctly."""
        provider = CLIModelProvider()

        # Test "cli:xxx" format
        assert provider._get_cli_client_name("cli:gemini") == "gemini"
        assert provider._get_cli_client_name("cli:kimi") == "kimi"
        assert provider._get_cli_client_name("cli:qwen") == "qwen"

    def test_validate_model_name_with_cli_prefix(self):
        """Test validate_model_name handles cli: prefix correctly.
        
        This is critical for get_provider_for_model() routing.
        """
        provider = CLIModelProvider()

        # Mock clink registry to have these clients available
        with patch.object(provider, "_is_cli_available", return_value=True):
            # cli:xxx format should be validated
            assert provider.validate_model_name("cli:gemini")
            assert provider.validate_model_name("cli:kimi")
            assert provider.validate_model_name("cli:qwen")
            # Case insensitive
            assert provider.validate_model_name("CLI:kimi")
            assert provider.validate_model_name("Cli:Gemini")

        # Non-cli models should not be validated
        assert not provider.validate_model_name("gpt-4")
        assert not provider.validate_model_name("gemini-2.5-pro")

    def test_validate_model_name_via_registry(self):
        """Test validate_model_name works via registry aliases."""
        provider = CLIModelProvider()

        # Registry-based canonical names should work
        assert provider.validate_model_name("cli:gemini")
        assert provider.validate_model_name("cli:kimi")

    def test_validate_model_name_via_aliases(self):
        """Test validate_model_name works via CLI model aliases.
        
        This ensures aliases like 'kimi cli', 'gemini-cli', 'gcli' are recognized.
        """
        provider = CLIModelProvider()

        # All these alias formats should resolve to CLI models
        cli_aliases = [
            # Claude CLI aliases
            "claude cli", "claude-cli", "ccli",
            # Gemini CLI aliases
            "gemini cli", "gemini-cli", "gcli",
            # Codex CLI aliases
            "codex cli", "codex-cli", "openai cli", "openai-cli", "ocli",
            # Kimi CLI aliases
            "kimi cli", "kimi-cli", "moonshot cli", "moonshot-cli", "kcli",
            # iFlow CLI aliases
            "iflow cli", "iflow-cli", "minimax cli", "icli",
            # Qwen CLI aliases
            "qwen cli", "qwen-cli", "tongyi cli", "tongyi-cli", "qcli",
            # Vecli aliases
            "vecli", "doubao cli", "doubao-cli", "vcli",
        ]
        
        for alias in cli_aliases:
            assert provider.validate_model_name(alias), f"Alias '{alias}' should be valid"

    def test_non_cli_names_not_validated(self):
        """Test that plain model names without 'cli' are NOT validated as CLI models.
        
        This is critical: 'kimi' should NOT route to CLI, only 'kimi cli' or 'cli:kimi' should.
        """
        provider = CLIModelProvider()

        # Non-CLI model names should NOT be validated
        non_cli_names = ["kimi", "gemini", "qwen", "claude", "codex", "iflow", "doubao"]
        for name in non_cli_names:
            assert not provider.validate_model_name(name), f"'{name}' should NOT be a CLI model"

    def test_supports_model_with_prefix(self):
        """Test supports_model recognizes cli: prefix."""
        provider = CLIModelProvider()

        # These should be supported (if clink registry has them)
        # We mock clink registry to avoid dependency on actual CLI installation
        with patch.object(provider, "_is_cli_available", return_value=True):
            assert provider.supports_model("cli:gemini")
            assert provider.supports_model("cli:kimi")

        # Non-cli models should not be supported
        assert not provider.supports_model("gpt-4")
        assert not provider.supports_model("gemini-2.5-pro")

    def test_supports_model_via_registry(self):
        """Test supports_model works via registry aliases."""
        provider = CLIModelProvider()

        # Registry-based aliases should work
        # Note: This tests the registry lookup, not actual CLI availability
        assert provider.supports_model("gemini cli") or provider.supports_model("cli:gemini")

    @patch("clink.get_registry")
    def test_is_cli_available(self, mock_get_registry):
        """Test _is_cli_available checks clink registry."""
        mock_registry = MagicMock()
        mock_registry.list_clients.return_value = ["gemini", "kimi", "qwen"]
        mock_get_registry.return_value = mock_registry

        provider = CLIModelProvider()
        # Force reload clink registry
        provider._clink_registry = None

        assert provider._is_cli_available("gemini")
        assert provider._is_cli_available("kimi")
        assert not provider._is_cli_available("nonexistent")

    @patch("clink.get_registry")
    @patch("clink.agents.create_agent")
    @patch("asyncio.run")
    def test_generate_content_calls_agent(self, mock_asyncio_run, mock_create_agent, mock_get_registry):
        """Test generate_content creates and runs CLI agent."""
        # Setup mocks
        mock_registry = MagicMock()
        mock_registry.list_clients.return_value = ["gemini"]
        mock_client = MagicMock()
        mock_role = MagicMock()
        mock_client.get_role.return_value = mock_role
        mock_registry.get_client.return_value = mock_client
        mock_get_registry.return_value = mock_registry

        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        # Mock agent output
        mock_output = MagicMock()
        mock_output.parsed.content = "Test response from CLI"
        mock_output.parsed.metadata = {}
        mock_output.parser_name = "test_parser"
        mock_output.returncode = 0
        mock_output.duration_seconds = 1.5
        mock_output.stdout = "stdout content"
        mock_asyncio_run.return_value = mock_output

        provider = CLIModelProvider()
        provider._clink_registry = None  # Force reload

        response = provider.generate_content(
            prompt="Hello CLI",
            model_name="cli:gemini",
            system_prompt="Be helpful",
        )

        # Verify agent was created and run
        mock_create_agent.assert_called_once_with(mock_client)
        mock_asyncio_run.assert_called_once()

        # Verify response
        assert response.content == "Test response from CLI"
        assert response.provider == ProviderType.CLI
        assert response.metadata["cli_name"] == "gemini"

    @patch("clink.get_registry")
    def test_generate_content_raises_for_unavailable_cli(self, mock_get_registry):
        """Test generate_content raises ValueError for unavailable CLI."""
        mock_registry = MagicMock()
        mock_registry.list_clients.return_value = ["gemini"]  # Only gemini available
        mock_get_registry.return_value = mock_registry

        provider = CLIModelProvider()
        provider._clink_registry = None

        with pytest.raises(ValueError, match="CLI 'nonexistent' not configured"):
            provider.generate_content(
                prompt="Hello",
                model_name="cli:nonexistent",
            )

    def test_convert_to_model_response(self):
        """Test _convert_to_model_response creates correct ModelResponse."""
        provider = CLIModelProvider()

        # Mock agent output
        mock_output = MagicMock()
        mock_output.parsed.content = "Response content"
        mock_output.parsed.metadata = {"key": "value"}
        mock_output.parser_name = "test_parser"
        mock_output.returncode = 0
        mock_output.duration_seconds = 2.0
        mock_output.stdout = "x" * 400  # ~100 tokens

        response = provider._convert_to_model_response(mock_output, "cli:test", "test")

        assert response.content == "Response content"
        assert response.provider == ProviderType.CLI
        assert response.model_name == "cli:test"
        assert response.friendly_name == "CLI (test)"
        assert response.metadata["cli_name"] == "test"
        assert response.metadata["parser"] == "test_parser"
        assert response.metadata["returncode"] == 0
        assert response.metadata["duration_seconds"] == 2.0
        assert "input_tokens" in response.usage
        assert "output_tokens" in response.usage


class TestCLIProviderRegistry:
    """Test CLI Provider registration with ModelProviderRegistry."""

    def test_cli_provider_registered(self):
        """Test CLIModelProvider is registered in ModelProviderRegistry."""
        from providers import ModelProviderRegistry

        # CLI should be in the priority order
        assert ProviderType.CLI in ModelProviderRegistry.PROVIDER_PRIORITY_ORDER

        # CLI should be after CUSTOM and before OPENROUTER
        order = ModelProviderRegistry.PROVIDER_PRIORITY_ORDER
        cli_idx = order.index(ProviderType.CLI)
        custom_idx = order.index(ProviderType.CUSTOM)
        openrouter_idx = order.index(ProviderType.OPENROUTER)

        assert cli_idx > custom_idx
        assert cli_idx < openrouter_idx

    @patch("clink.get_registry")
    def test_get_provider_returns_cli_provider(self, mock_get_registry):
        """Test ModelProviderRegistry.get_provider returns CLIModelProvider."""
        from providers import ModelProviderRegistry

        # Mock clink registry to return some clients
        mock_clink_registry = MagicMock()
        mock_clink_registry.list_clients.return_value = ["gemini", "kimi"]
        mock_get_registry.return_value = mock_clink_registry

        # Clear any cached instances
        ModelProviderRegistry.clear_cache()

        provider = ModelProviderRegistry.get_provider(ProviderType.CLI)

        assert provider is not None
        assert isinstance(provider, CLIModelProvider)

    @patch("clink.get_registry")
    def test_get_provider_returns_none_when_no_cli_clients(self, mock_get_registry):
        """Test ModelProviderRegistry.get_provider returns None when no CLI clients."""
        from providers import ModelProviderRegistry

        # Mock clink registry to return empty list
        mock_clink_registry = MagicMock()
        mock_clink_registry.list_clients.return_value = []
        mock_get_registry.return_value = mock_clink_registry

        # Clear any cached instances
        ModelProviderRegistry.clear_cache()

        provider = ModelProviderRegistry.get_provider(ProviderType.CLI)

        assert provider is None


class TestCLISuggestion:
    """Test CLI suggestion in error messages."""

    def test_cli_suggestion_for_known_names(self):
        """Test _get_cli_suggestion returns suggestions for known CLI base names."""
        from tools.chat import ChatTool

        tool = ChatTool()

        # Should return suggestions for known CLI base names
        suggestion = tool._get_cli_suggestion("kimi")
        assert suggestion is not None
        assert "cli:kimi" in suggestion
        assert "kcli" in suggestion

        suggestion = tool._get_cli_suggestion("gemini")
        assert suggestion is not None
        assert "cli:gemini" in suggestion
        assert "gcli" in suggestion

        suggestion = tool._get_cli_suggestion("iflow")
        assert suggestion is not None
        assert "cli:iflow" in suggestion
        assert "icli" in suggestion

    def test_cli_suggestion_case_insensitive(self):
        """Test _get_cli_suggestion is case insensitive."""
        from tools.chat import ChatTool

        tool = ChatTool()

        # Should work with different cases
        assert tool._get_cli_suggestion("KIMI") is not None
        assert tool._get_cli_suggestion("Kimi") is not None
        assert tool._get_cli_suggestion("kimi") is not None

    def test_cli_suggestion_returns_none_for_unknown(self):
        """Test _get_cli_suggestion returns None for unknown model names."""
        from tools.chat import ChatTool

        tool = ChatTool()

        # Should return None for non-CLI model names
        assert tool._get_cli_suggestion("gpt-4") is None
        assert tool._get_cli_suggestion("gemini-2.5-pro") is None
        assert tool._get_cli_suggestion("random-model") is None
        # CLI format names should not trigger suggestion
        assert tool._get_cli_suggestion("cli:kimi") is None
        assert tool._get_cli_suggestion("kcli") is None
