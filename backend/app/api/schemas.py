from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# Provider Schemas
class ProviderResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    base_api_url: Optional[str]
    schema_version: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


# API Key Schemas
class APIKeyCreate(BaseModel):
    provider_id: UUID
    label: str
    api_key_value: str  # Plain text, will be encrypted server-side


class APIKeyResponse(BaseModel):
    id: UUID
    provider_id: UUID
    label: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class APIKeyUpdate(BaseModel):
    label: Optional[str] = None
    is_active: Optional[bool] = None


# Project Schemas
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# Import Job Schemas
class ImportJobCreate(BaseModel):
    provider_id: UUID
    api_key_id: UUID
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class ImportJobResponse(BaseModel):
    id: UUID
    provider_id: UUID
    api_key_id: UUID
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    summary: Optional[str]
    error_details: Optional[str]
    conversations_imported: int
    messages_imported: int
    artifacts_imported: int

    class Config:
        from_attributes = True


# Message Schemas
class MessageResponse(BaseModel):
    id: UUID
    provider_message_id: Optional[str]
    role: str
    created_at: Optional[datetime]
    sequence_index: int
    content: str
    raw_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


# Artifact Schemas
class ArtifactResponse(BaseModel):
    id: UUID
    artifact_type: str
    provider_artifact_id: Optional[str]
    filename: Optional[str]
    mime_type: Optional[str]
    storage_path: Optional[str]
    download_status: str
    download_error: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


# Conversation Schemas
class ConversationListItem(BaseModel):
    id: UUID
    provider_id: UUID
    title: Optional[str]
    started_at: Optional[datetime]
    message_count: int = 0
    has_artifacts: bool = False
    projects: List[str] = []

    class Config:
        from_attributes = True


class ConversationDetail(BaseModel):
    id: UUID
    provider_id: UUID
    provider_conversation_id: Optional[str]
    title: Optional[str]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    origin: str
    archived: bool
    messages: List[MessageResponse]
    artifacts: List[ArtifactResponse]
    projects: List[ProjectResponse]

    class Config:
        from_attributes = True


class ConversationProjectAssign(BaseModel):
    project_id: UUID


# Pagination
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
