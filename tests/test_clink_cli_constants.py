"""Test clink CLI constants and parser configurations.

This test validates that the parser configurations in constants.py match
the actual CLI command-line options and output formats.
"""

import pytest

from clink.constants import INTERNAL_DEFAULTS
from clink.parsers import get_parser


class TestCLIConstants:
    """Verify that CLI constants are properly configured."""

    def test_all_cli_parsers_exist(self):
        """Ensure all CLIs have parsers that can be instantiated."""
        for cli_name, defaults in INTERNAL_DEFAULTS.items():
            parser_name = defaults.parser
            try:
                parser = get_parser(parser_name)
                assert parser is not None
                assert hasattr(parser, "parse")
            except Exception as e:
                pytest.fail(f"Failed to get parser '{parser_name}' for CLI '{cli_name}': {e}")

    def test_gemini_configuration(self):
        """Verify gemini CLI configuration matches its --help output."""
        config = INTERNAL_DEFAULTS["gemini"]
        assert config.parser == "gemini_json"
        assert config.additional_args == ["-o", "json"]
        # gemini supports: -o, --output-format [text|json|stream-json]

    def test_codex_configuration(self):
        """Verify codex CLI configuration matches its --help output."""
        config = INTERNAL_DEFAULTS["codex"]
        assert config.parser == "codex_jsonl"
        assert config.additional_args == ["exec"]
        # codex uses 'exec' subcommand for non-interactive mode with JSONL output

    def test_claude_configuration(self):
        """Verify claude CLI configuration matches its --help output."""
        config = INTERNAL_DEFAULTS["claude"]
        assert config.parser == "claude_json"
        assert config.additional_args == ["--print", "--output-format", "json"]
        # claude supports: --print --output-format [text|json|stream-json]

    def test_iflow_configuration(self):
        """Verify iflow CLI configuration."""
        config = INTERNAL_DEFAULTS["iflow"]
        # iflow outputs plain text, not JSON
        assert config.parser == "iflow_plain"

    def test_kimi_configuration(self):
        """Verify kimi CLI configuration."""
        config = INTERNAL_DEFAULTS["kimi"]
        # kimi outputs mixed format (ThinkPart, TextPart, etc) in plain text mode
        assert config.parser == "kimi_plain"

    def test_qwen_configuration(self):
        """Verify qwen CLI configuration."""
        config = INTERNAL_DEFAULTS["qwen"]
        # qwen supports: -o, --output-format [text|json]
        assert config.parser in ["gemini_json", "claude_json"]

    def test_vecli_configuration(self):
        """Verify vecli CLI configuration."""
        config = INTERNAL_DEFAULTS["vecli"]
        # vecli outputs plain text, not JSON
        assert config.parser == "vecli_plain"

    def test_all_parsers_have_required_defaults(self):
        """Ensure all CLIs have required default fields."""
        for cli_name, defaults in INTERNAL_DEFAULTS.items():
            assert defaults.parser, f"{cli_name} missing parser"
            assert defaults.additional_args is not None, f"{cli_name} missing additional_args"
            assert defaults.default_role_prompt, f"{cli_name} missing default_role_prompt"
            assert defaults.runner, f"{cli_name} missing runner"
