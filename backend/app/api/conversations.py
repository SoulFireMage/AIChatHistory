from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..models import Conversation, Message, Artifact, Project, ConversationProject, Provider
from .schemas import (
    ConversationListItem,
    ConversationDetail,
    ConversationProjectAssign,
    MessageResponse,
    ArtifactResponse,
    ProjectResponse
)

router = APIRouter()


@router.get("", response_model=List[ConversationListItem])
def list_conversations(
    provider_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    search: Optional[str] = None,
    has_artifacts: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    List conversations with filtering and pagination.

    Filters:
    - provider_id: Filter by provider
    - project_id: Filter by project
    - from_date/to_date: Filter by conversation start date
    - search: Search in titles and message content
    - has_artifacts: Filter conversations with/without artifacts
    """
    query = db.query(Conversation)

    # Apply filters
    if provider_id:
        query = query.filter(Conversation.provider_id == provider_id)

    if project_id:
        query = query.join(ConversationProject).filter(
            ConversationProject.project_id == project_id
        )

    if from_date:
        query = query.filter(Conversation.started_at >= from_date)

    if to_date:
        query = query.filter(Conversation.started_at <= to_date)

    if search:
        # Search in conversation titles and message content
        search_term = f"%{search}%"
        query = query.outerjoin(Message).filter(
            or_(
                Conversation.title.ilike(search_term),
                Message.content.ilike(search_term)
            )
        ).distinct()

    if has_artifacts is not None:
        if has_artifacts:
            query = query.join(Artifact).distinct()
        else:
            query = query.outerjoin(Artifact).filter(Artifact.id.is_(None))

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    conversations = query.order_by(Conversation.started_at.desc()).offset(offset).limit(page_size).all()

    # Build response with message counts and projects
    result = []
    for conv in conversations:
        message_count = db.query(func.count(Message.id)).filter(
            Message.conversation_id == conv.id
        ).scalar()

        has_artifacts_flag = db.query(
            db.query(Artifact).filter(Artifact.conversation_id == conv.id).exists()
        ).scalar()

        projects = db.query(Project).join(ConversationProject).filter(
            ConversationProject.conversation_id == conv.id
        ).all()

        result.append(ConversationListItem(
            id=conv.id,
            provider_id=conv.provider_id,
            title=conv.title,
            started_at=conv.started_at,
            message_count=message_count,
            has_artifacts=has_artifacts_flag,
            projects=[p.name for p in projects]
        ))

    return result


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db)
):
    """Get full conversation details including messages and artifacts."""
    conversation = db.query(Conversation).options(
        joinedload(Conversation.messages),
        joinedload(Conversation.artifacts),
        joinedload(Conversation.conversation_projects).joinedload(ConversationProject.project)
    ).filter(Conversation.id == conversation_id).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Sort messages by sequence
    messages = sorted(conversation.messages, key=lambda m: m.sequence_index)

    # Get projects
    projects = [cp.project for cp in conversation.conversation_projects]

    return ConversationDetail(
        id=conversation.id,
        provider_id=conversation.provider_id,
        provider_conversation_id=conversation.provider_conversation_id,
        title=conversation.title,
        started_at=conversation.started_at,
        ended_at=conversation.ended_at,
        origin=conversation.origin,
        archived=conversation.archived,
        messages=[MessageResponse.model_validate(m) for m in messages],
        artifacts=[ArtifactResponse.model_validate(a) for a in conversation.artifacts],
        projects=[ProjectResponse.model_validate(p) for p in projects]
    )


@router.post("/{conversation_id}/projects")
def assign_project_to_conversation(
    conversation_id: UUID,
    data: ConversationProjectAssign,
    db: Session = Depends(get_db)
):
    """Assign a project to a conversation."""
    # Verify conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify project exists
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if already assigned
    existing = db.query(ConversationProject).filter(
        ConversationProject.conversation_id == conversation_id,
        ConversationProject.project_id == data.project_id
    ).first()

    if existing:
        return {"message": "Project already assigned to conversation"}

    # Create assignment
    cp = ConversationProject(
        conversation_id=conversation_id,
        project_id=data.project_id
    )
    db.add(cp)
    db.commit()

    return {"message": "Project assigned successfully"}


@router.delete("/{conversation_id}/projects/{project_id}")
def remove_project_from_conversation(
    conversation_id: UUID,
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Remove a project from a conversation."""
    cp = db.query(ConversationProject).filter(
        ConversationProject.conversation_id == conversation_id,
        ConversationProject.project_id == project_id
    ).first()

    if not cp:
        raise HTTPException(status_code=404, detail="Project assignment not found")

    db.delete(cp)
    db.commit()

    return {"message": "Project removed from conversation"}


@router.get("/{conversation_id}/export-markdown")
def export_conversation_to_markdown(
    conversation_id: UUID,
    db: Session = Depends(get_db)
):
    """Export a conversation to Markdown format."""
    conversation = db.query(Conversation).options(
        joinedload(Conversation.messages),
        joinedload(Conversation.artifacts),
        joinedload(Conversation.conversation_projects).joinedload(ConversationProject.project)
    ).filter(Conversation.id == conversation_id).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get provider info
    provider = db.query(Provider).filter(Provider.id == conversation.provider_id).first()

    # Build Markdown content
    md_lines = []

    # Title
    title = conversation.title or "Untitled Conversation"
    md_lines.append(f"# {title}\n")

    # Metadata
    md_lines.append("## Metadata\n")
    md_lines.append(f"- **Provider:** {provider.display_name if provider else 'Unknown'}")
    md_lines.append(f"- **Conversation ID:** {conversation.provider_conversation_id or 'N/A'}")
    if conversation.started_at:
        md_lines.append(f"- **Started:** {conversation.started_at.isoformat()}")
    if conversation.ended_at:
        md_lines.append(f"- **Ended:** {conversation.ended_at.isoformat()}")

    # Projects
    projects = [cp.project for cp in conversation.conversation_projects]
    if projects:
        project_names = ", ".join(p.name for p in projects)
        md_lines.append(f"- **Projects:** {project_names}")

    md_lines.append("\n---\n")

    # Messages
    md_lines.append("## Conversation\n")
    messages = sorted(conversation.messages, key=lambda m: m.sequence_index)

    for msg in messages:
        role_display = msg.role.capitalize()
        md_lines.append(f"**{role_display}:**\n")
        md_lines.append(f"{msg.content}\n")

    # Artifacts
    if conversation.artifacts:
        md_lines.append("\n---\n")
        md_lines.append("## Attachments\n")
        for artifact in conversation.artifacts:
            filename = artifact.filename or "Unknown"
            artifact_type = artifact.artifact_type
            status = artifact.download_status
            md_lines.append(f"- **{filename}** ({artifact_type}, status: {status})")
            if artifact.storage_path:
                md_lines.append(f"  - Path: {artifact.storage_path}")
            if artifact.download_error:
                md_lines.append(f"  - Error: {artifact.download_error}")
            md_lines.append("")

    markdown_content = "\n".join(md_lines)

    # Return as downloadable file
    filename = f"{conversation.id}.md"
    return Response(
        content=markdown_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
