"""Registry loader for CLI model capabilities."""

from __future__ import annotations

from ..shared import ProviderType
from .base import CapabilityModelRegistry


class CLIModelRegistry(CapabilityModelRegistry):
    """Capability registry backed by ``conf/cli_models.json``.

    This registry maps CLI model names (e.g., "cli:gemini", "kimi cli") to their
    capabilities. The actual CLI execution is handled by the clink subsystem;
    this registry only provides metadata for model selection and capability checking.
    """

    def __init__(self, config_path: str | None = None) -> None:
        super().__init__(
            env_var_name="CLI_MODELS_CONFIG_PATH",
            default_filename="cli_models.json",
            provider=ProviderType.CLI,
            friendly_prefix="CLI ({model})",
            config_path=config_path,
        )

    def _extra_keys(self) -> set[str]:
        """Allow cli_client field to pass through for routing."""
        return {"cli_client"}
