"""
Provider Manager - Unified provider discovery and selection.

Provides a single interface for:
- Discovering configured providers
- Selecting preferred provider based on priority
- Listing available models across providers
"""

import logging
from typing import Optional

from utils.env import get_env

logger = logging.getLogger(__name__)


class ProviderManager:
    """Unified provider discovery and selection.
    
    Wraps the existing ModelProviderRegistry with convenience methods
    for provider discovery and intelligent selection.
    """
    
    # Provider priority order (higher = preferred)
    # This matches the registry's PROVIDER_PRIORITY_ORDER
    PROVIDER_PRIORITY = [
        "gemini",      # Google Gemini - fast and capable
        "openai",      # OpenAI - reliable fallback
        "azure",       # Azure OpenAI - enterprise
        "xai",         # X.AI Grok
        "anthropic",   # Anthropic Claude (via API)
        "openrouter",  # OpenRouter aggregator
        "cli",         # CLI agents (always available)
    ]
    
    # Environment variable mapping
    PROVIDER_ENV_KEYS = {
        "gemini": "GOOGLE_API_KEY",
        "openai": "OPENAI_API_KEY",
        "azure": "AZURE_OPENAI_API_KEY",
        "xai": "XAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "cli": None,  # CLI doesn't need API key
    }
    
    def __init__(self) -> None:
        """Initialize provider manager."""
        self._configured_cache: Optional[list[str]] = None
    
    def get_configured_providers(self, include_cli: bool = True) -> list[str]:
        """Get list of providers that have API keys configured.
        
        Args:
            include_cli: Whether to include CLI provider (always available)
            
        Returns:
            List of configured provider names
        """
        if self._configured_cache is not None:
            result = list(self._configured_cache)
            if not include_cli and "cli" in result:
                result.remove("cli")
            return result
        
        configured = []
        
        for provider, env_key in self.PROVIDER_ENV_KEYS.items():
            if env_key is None:
                # CLI is always available
                configured.append(provider)
            elif get_env(env_key):
                configured.append(provider)
        
        self._configured_cache = configured
        
        if not include_cli and "cli" in configured:
            return [p for p in configured if p != "cli"]
        
        return list(configured)
    
    def is_provider_configured(self, provider: str) -> bool:
        """Check if a specific provider is configured.
        
        Args:
            provider: Provider name to check
            
        Returns:
            True if provider is configured and available
        """
        return provider.lower() in self.get_configured_providers()
    
    def get_preferred_provider(
        self,
        hints: Optional[list[str]] = None,
        exclude_cli: bool = False,
    ) -> Optional[str]:
        """Get the preferred provider based on priority and configuration.
        
        Args:
            hints: Optional list of preferred providers (checked first)
            exclude_cli: Whether to exclude CLI from selection
            
        Returns:
            Name of the best available provider, or None if none configured
        """
        configured = self.get_configured_providers(include_cli=not exclude_cli)
        
        if not configured:
            return None
        
        # Check hints first
        if hints:
            for hint in hints:
                hint_lower = hint.lower()
                if hint_lower in configured:
                    return hint_lower
        
        # Fall back to priority order
        for provider in self.PROVIDER_PRIORITY:
            if provider in configured:
                if exclude_cli and provider == "cli":
                    continue
                return provider
        
        # Return first available if none in priority
        return configured[0] if configured else None
    
    def get_available_models(self) -> dict[str, list[str]]:
        """Get all available models grouped by provider.
        
        Returns:
            Dictionary mapping provider names to list of model names
        """
        try:
            from providers.registry import ModelProviderRegistry
            from providers.shared import ProviderType
            
            registry = ModelProviderRegistry()
            result = {}
            
            # Map provider names to ProviderType
            provider_type_map = {
                "gemini": ProviderType.GOOGLE,
                "openai": ProviderType.OPENAI,
                "azure": ProviderType.AZURE,
                "xai": ProviderType.XAI,
                "cli": ProviderType.CLI,
                "openrouter": ProviderType.OPENROUTER,
            }
            
            for provider_name in self.get_configured_providers():
                provider_type = provider_type_map.get(provider_name)
                if provider_type:
                    provider = registry.get_provider(provider_type)
                    if provider:
                        models = provider.list_models(respect_restrictions=True)
                        if models:
                            result[provider_name] = models
            
            return result
        except Exception as e:
            logger.warning(f"Failed to get available models: {e}")
            return {}
    
    def invalidate_cache(self) -> None:
        """Invalidate the configured providers cache.
        
        Call this if environment variables change at runtime.
        """
        self._configured_cache = None


# Global singleton
_manager: Optional[ProviderManager] = None


def get_provider_manager() -> ProviderManager:
    """Get the global provider manager instance."""
    global _manager
    if _manager is None:
        _manager = ProviderManager()
    return _manager
