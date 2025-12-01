"""CLI Model Provider - bridges ModelProvider interface to clink CLI agents.

This provider enables any Zen MCP tool (chat, thinkdeep, consensus, etc.) to
transparently use CLI backends by specifying model names like:
- "cli:gemini" or "gemini cli"
- "cli:kimi" or "kimi-cli"
- "cli:qwen" or "qwen cli"

The provider resolves model → CLI client, creates a clink agent, executes,
and returns a standard ModelResponse.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from typing import TYPE_CHECKING, ClassVar, Optional

if TYPE_CHECKING:
    from clink.agents.base import AgentOutput

from .base import ModelProvider
from .registries.cli import CLIModelRegistry
from .registry_provider_mixin import RegistryBackedProviderMixin
from .shared import ModelCapabilities, ModelResponse, ProviderType

logger = logging.getLogger(__name__)


class CLIModelProvider(RegistryBackedProviderMixin, ModelProvider):
    """Provider that routes requests to clink CLI agents.

    This allows tools to use CLI backends through the standard ModelProvider
    interface without needing to know about clink internals.
    """

    REGISTRY_CLASS = CLIModelRegistry
    MODEL_CAPABILITIES: ClassVar[dict[str, ModelCapabilities]] = {}

    def __init__(self, api_key: str = "", **kwargs):
        """Initialize CLI provider.

        Args:
            api_key: Not used for CLI provider, accepts any value for interface compatibility.
            **kwargs: Additional configuration options.
        """
        self._ensure_registry()
        # CLI provider doesn't need a real API key
        super().__init__(api_key or "cli-no-key", **kwargs)
        self._clink_registry = None
        self._invalidate_capability_cache()

    @property
    def clink_registry(self):
        """Lazy load clink registry."""
        if self._clink_registry is None:
            from clink import get_registry

            self._clink_registry = get_registry()
        return self._clink_registry

    def get_provider_type(self) -> ProviderType:
        """Return the CLI provider type."""
        return ProviderType.CLI

    def _get_cli_client_name(self, model_name: str) -> str:
        """Extract CLI client name from model name.

        Examples:
            "cli:gemini" -> "gemini"
            "cli:kimi" -> "kimi"
        """
        resolved = self._resolve_model_name(model_name)

        # Handle "cli:xxx" format
        if resolved.startswith("cli:"):
            return resolved[4:]

        # Try to get cli_client from registry extras
        if self._registry:
            entry = self._registry.get_entry(resolved)
            if entry and "cli_client" in entry:
                return entry["cli_client"]

        # Fallback: strip "cli:" prefix if present
        return resolved.replace("cli:", "")

    def _is_cli_available(self, cli_name: str) -> bool:
        """Check if CLI client is configured in clink."""
        try:
            return cli_name in self.clink_registry.list_clients()
        except Exception:
            return False

    def validate_model_name(self, model_name: str) -> bool:
        """Check if model name is valid for CLI provider.

        Handles both registry-based validation and cli: prefix format.
        This override is critical for get_provider_for_model() to correctly
        route cli:xxx models to this provider.
        """
        # First try base class validation (registry-based aliases)
        try:
            if super().validate_model_name(model_name):
                return True
        except Exception:
            pass

        # Also accept "cli:xxx" prefix if the CLI client is available
        if model_name.lower().startswith("cli:"):
            cli_name = model_name[4:]
            return self._is_cli_available(cli_name)

        return False

    def supports_model(self, model_name: str) -> bool:
        """Check if this provider supports the given model."""
        # Delegate to validate_model_name which now handles both cases
        return self.validate_model_name(model_name)

    def generate_content(
        self,
        prompt: str,
        model_name: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.5,
        max_output_tokens: Optional[int] = None,
        **kwargs,
    ) -> ModelResponse:
        """Generate content by calling the appropriate CLI agent.

        Args:
            prompt: The user prompt to send to the CLI.
            model_name: CLI model identifier (e.g., "cli:gemini", "kimi cli").
            system_prompt: Optional system instructions.
            temperature: Not used by CLI (ignored).
            max_output_tokens: Not used by CLI (ignored).
            **kwargs: Additional arguments including:
                - role: CLI role to use (default: "default")
                - files: List of file paths
                - images: List of image paths

        Returns:
            ModelResponse with the CLI output.

        Raises:
            ValueError: If CLI is not configured.
            RuntimeError: If CLI execution fails.
        """
        from clink.agents import CLIAgentError, create_agent

        cli_name = self._get_cli_client_name(model_name)

        if not self._is_cli_available(cli_name):
            available = self.clink_registry.list_clients()
            raise ValueError(
                f"CLI '{cli_name}' not configured. Available: {', '.join(available) if available else 'none'}"
            )

        client = self.clink_registry.get_client(cli_name)
        role_name = kwargs.get("role", "default")
        role = client.get_role(role_name)
        agent = create_agent(client)

        files = kwargs.get("files", []) or []
        images = kwargs.get("images", []) or []

        logger.info(f"CLI Provider: Invoking {cli_name} with role={role_name}")

        # Run async agent safely in both sync and async contexts
        try:
            result = self._run_agent_safely(
                agent=agent,
                role=role,
                prompt=prompt,
                system_prompt=system_prompt,
                files=files,
                images=images,
            )
        except CLIAgentError as e:
            logger.error(f"CLI '{cli_name}' failed: {e}")
            raise RuntimeError(f"CLI '{cli_name}' failed: {e}") from e

        return self._convert_to_model_response(result, model_name, cli_name)

    def _run_agent_safely(
        self,
        agent,
        role,
        prompt: str,
        system_prompt: Optional[str],
        files: list,
        images: list,
    ):
        """Run async agent safely, handling both sync and async contexts.

        When called from an async context (running event loop), runs the agent
        in a separate thread with its own event loop to avoid conflicts.
        When called from a sync context, uses asyncio.run() directly.
        """

        async def run_agent():
            return await agent.run(
                role=role,
                prompt=prompt,
                system_prompt=system_prompt,
                files=files,
                images=images,
            )

        def run_in_new_loop():
            """Create a new event loop in this thread and run the agent."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(run_agent())
            finally:
                loop.close()

        # Check if we're in an async context (running event loop)
        try:
            asyncio.get_running_loop()
            # We're in an async context - run in a separate thread to avoid conflict
            logger.debug("Running CLI agent in separate thread (async context detected)")
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_in_new_loop)
                return future.result()
        except RuntimeError:
            # No running loop - safe to use asyncio.run() directly
            logger.debug("Running CLI agent directly (no async context)")
            return asyncio.run(run_agent())

    # Large metadata fields that should be pruned to prevent memory/token issues
    _LARGE_METADATA_FIELDS = ["raw_stdout", "raw_output_file", "raw", "thinking_content", "events"]

    def _convert_to_model_response(
        self,
        agent_output: "AgentOutput",
        model_name: str,
        cli_name: str,
    ) -> ModelResponse:
        """Convert clink AgentOutput to standard ModelResponse."""
        content = agent_output.parsed.content

        metadata = agent_output.parsed.metadata.copy() if agent_output.parsed.metadata else {}
        
        # Prune large fields from metadata to prevent memory/token overflow
        pruned_fields = []
        for field in self._LARGE_METADATA_FIELDS:
            if field in metadata:
                metadata.pop(field)
                pruned_fields.append(field)
        if pruned_fields:
            metadata["_pruned_fields"] = pruned_fields
        
        metadata.update(
            {
                "cli_name": cli_name,
                "parser": agent_output.parser_name,
                "returncode": agent_output.returncode,
                "duration_seconds": agent_output.duration_seconds,
            }
        )

        # Token estimation (CLI doesn't provide actual counts)
        est_output = max(1, len(content) // 4)
        est_input = max(1, len(agent_output.stdout) // 4)

        return ModelResponse(
            content=content,
            usage={
                "input_tokens": est_input,
                "output_tokens": est_output,
                "total_tokens": est_input + est_output,
            },
            model_name=model_name,
            friendly_name=f"CLI ({cli_name})",
            provider=ProviderType.CLI,
            metadata=metadata,
        )
