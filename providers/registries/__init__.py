"""Registry implementations for provider capability manifests."""

from .azure import AzureModelRegistry
from .cli import CLIModelRegistry
from .custom import CustomEndpointModelRegistry
from .dial import DialModelRegistry
from .gemini import GeminiModelRegistry
from .openai import OpenAIModelRegistry
from .openrouter import OpenRouterModelRegistry
from .xai import XAIModelRegistry

__all__ = [
    "AzureModelRegistry",
    "CLIModelRegistry",
    "CustomEndpointModelRegistry",
    "DialModelRegistry",
    "GeminiModelRegistry",
    "OpenAIModelRegistry",
    "OpenRouterModelRegistry",
    "XAIModelRegistry",
]
