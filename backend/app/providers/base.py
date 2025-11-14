from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class ProviderMessage:
    """Normalized message from any provider."""
    provider_message_id: Optional[str]
    role: str  # 'user', 'assistant', 'system', 'tool', etc.
    content: str
    created_at: Optional[datetime]
    sequence_index: int
    raw_metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProviderArtifact:
    """Normalized artifact/attachment from any provider."""
    provider_artifact_id: Optional[str]
    artifact_type: str  # 'file', 'image', 'canvas', 'code', 'other'
    filename: Optional[str]
    mime_type: Optional[str]
    content: Optional[bytes] = None  # Raw content if downloaded
    download_status: str = "pending"  # 'success', 'not_supported', 'error', 'pending'
    download_error: Optional[str] = None
    message_sequence_index: Optional[int] = None  # Link to specific message
    raw_metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProviderConversationSummary:
    """Lightweight conversation summary for listing."""
    provider_conversation_id: str
    title: Optional[str]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    message_count: Optional[int] = None
    raw_metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProviderConversationDetail:
    """Full conversation detail with messages and artifacts."""
    provider_conversation_id: str
    title: Optional[str]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    messages: List[ProviderMessage]
    artifacts: List[ProviderArtifact]
    raw_metadata: Optional[Dict[str, Any]] = None


class ConversationProviderAdapter(ABC):
    """
    Abstract base class for provider adapters.

    Each provider (OpenAI, Anthropic, etc.) implements this interface
    to provide a normalized way to import conversations.
    """

    @abstractmethod
    async def list_conversations(
        self,
        api_key: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[ProviderConversationSummary]:
        """
        List conversations from the provider.

        Args:
            api_key: The decrypted API key
            options: Optional filters like date range

        Returns:
            List of conversation summaries
        """
        pass

    @abstractmethod
    async def fetch_conversation(
        self,
        api_key: str,
        conversation_id: str
    ) -> ProviderConversationDetail:
        """
        Fetch full conversation details including messages.

        Args:
            api_key: The decrypted API key
            conversation_id: Provider-specific conversation ID

        Returns:
            Full conversation detail
        """
        pass

    @abstractmethod
    async def fetch_artifacts(
        self,
        api_key: str,
        conversation_detail: ProviderConversationDetail
    ) -> List[ProviderArtifact]:
        """
        Attempt to fetch artifacts/attachments for a conversation.

        Args:
            api_key: The decrypted API key
            conversation_detail: The conversation to fetch artifacts for

        Returns:
            List of artifacts (may include unsupported/failed items)
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'openai', 'anthropic')."""
        pass
