from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey,
    DateTime, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from ..database import Base


class Provider(Base):
    """LLM Provider (OpenAI, Anthropic, etc.)"""
    __tablename__ = "providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)  # e.g., "openai", "anthropic"
    display_name = Column(String(200), nullable=False)  # e.g., "ChatGPT", "Claude"
    base_api_url = Column(Text, nullable=True)
    schema_version = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    api_keys = relationship("APIKey", back_populates="provider")
    conversations = relationship("Conversation", back_populates="provider")
    import_jobs = relationship("ImportJob", back_populates="provider")


class APIKey(Base):
    """API Keys for accessing provider APIs"""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)
    label = Column(String(200), nullable=False)
    key_encrypted = Column(Text, nullable=False)  # Encrypted API key
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    provider = relationship("Provider", back_populates="api_keys")
    import_jobs = relationship("ImportJob", back_populates="api_key")


class Project(Base):
    """Projects for organizing conversations"""
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    conversation_projects = relationship("ConversationProject", back_populates="project")


class Conversation(Base):
    """Imported conversations"""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)
    provider_conversation_id = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    origin = Column(String(50), default="api")  # 'api', 'export', 'manual'
    import_job_id = Column(UUID(as_uuid=True), ForeignKey("import_jobs.id"), nullable=True)
    import_notes = Column(Text, nullable=True)
    archived = Column(Boolean, default=False, nullable=False)
    raw_metadata = Column(JSONB, nullable=True)

    # Relationships
    provider = relationship("Provider", back_populates="conversations")
    import_job = relationship("ImportJob", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="conversation", cascade="all, delete-orphan")
    conversation_projects = relationship("ConversationProject", back_populates="conversation", cascade="all, delete-orphan")
    edits = relationship("ConversationEdit", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('provider_id', 'provider_conversation_id', name='uq_provider_conversation'),
        Index('idx_conversation_started_at', 'started_at'),
        Index('idx_conversation_provider', 'provider_id'),
    )


class ConversationProject(Base):
    """Join table for conversations and projects"""
    __tablename__ = "conversation_projects"

    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), primary_key=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), primary_key=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="conversation_projects")
    project = relationship("Project", back_populates="conversation_projects")


class Message(Base):
    """Messages within conversations"""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    provider_message_id = Column(Text, nullable=True)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system', 'tool', etc.
    created_at = Column(DateTime(timezone=True), nullable=True)
    sequence_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    raw_metadata = Column(JSONB, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    artifacts = relationship("Artifact", back_populates="message")

    __table_args__ = (
        Index('idx_message_conversation', 'conversation_id'),
        Index('idx_message_sequence', 'conversation_id', 'sequence_index'),
    )


class Artifact(Base):
    """Artifacts/attachments associated with conversations"""
    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    artifact_type = Column(String(50), nullable=False)  # 'file', 'image', 'canvas', 'code', 'other'
    provider_artifact_id = Column(Text, nullable=True)
    filename = Column(Text, nullable=True)
    mime_type = Column(String(200), nullable=True)
    storage_path = Column(Text, nullable=True)
    download_status = Column(String(50), default="pending")  # 'success', 'not_supported', 'error', 'pending'
    download_error = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    raw_metadata = Column(JSONB, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="artifacts")
    message = relationship("Message", back_populates="artifacts")

    __table_args__ = (
        Index('idx_artifact_conversation', 'conversation_id'),
    )


class ImportJob(Base):
    """Import jobs for tracking conversation imports"""
    __tablename__ = "import_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="running")  # 'running', 'success', 'partial', 'failed'
    requested_range = Column(JSONB, nullable=True)  # e.g., {"from_date": "...", "to_date": "..."}
    summary = Column(Text, nullable=True)
    error_details = Column(Text, nullable=True)

    # Statistics
    conversations_imported = Column(Integer, default=0)
    messages_imported = Column(Integer, default=0)
    artifacts_imported = Column(Integer, default=0)

    # Relationships
    provider = relationship("Provider", back_populates="import_jobs")
    api_key = relationship("APIKey", back_populates="import_jobs")
    conversations = relationship("Conversation", back_populates="import_job")

    __table_args__ = (
        Index('idx_import_job_status', 'status'),
    )


class ConversationEdit(Base):
    """Edited/curated versions of conversations (v1.1+)"""
    __tablename__ = "conversation_edits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    label = Column(String(200), nullable=False)
    edited_markdown = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_modified_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    notes = Column(Text, nullable=True)
    base_conversation_hash = Column(String(64), nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="edits")
