from typing import Dict
from .base import ConversationProviderAdapter
from .openai_adapter import OpenAIAdapter
from .anthropic_adapter import AnthropicAdapter


class ProviderRegistry:
    """Registry for managing provider adapters."""

    def __init__(self):
        self._adapters: Dict[str, ConversationProviderAdapter] = {}
        self._register_default_providers()

    def _register_default_providers(self):
        """Register built-in provider adapters."""
        self.register(OpenAIAdapter())
        self.register(AnthropicAdapter())

    def register(self, adapter: ConversationProviderAdapter):
        """Register a provider adapter."""
        self._adapters[adapter.provider_name] = adapter

    def get_adapter(self, provider_name: str) -> ConversationProviderAdapter:
        """Get a provider adapter by name."""
        if provider_name not in self._adapters:
            raise ValueError(f"Unknown provider: {provider_name}")
        return self._adapters[provider_name]

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._adapters.keys())


# Global registry instance
provider_registry = ProviderRegistry()
