from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..models import ImportJob, APIKey, Provider, Conversation, Message, Artifact
from ..services import decrypt_api_key
from ..providers.registry import provider_registry
from .schemas import ImportJobCreate, ImportJobResponse

router = APIRouter()


async def run_import_job(job_id: UUID, db_url: str):
    """
    Background task to run an import job.

    This is a simplified implementation. In production, you might want to use
    Celery, RQ, or another task queue for better reliability.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create a new database session for the background task
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if not job:
            return

        # Get API key and decrypt it
        api_key_record = db.query(APIKey).filter(APIKey.id == job.api_key_id).first()
        if not api_key_record:
            job.status = "failed"
            job.error_details = "API key not found"
            job.finished_at = datetime.now()
            db.commit()
            return

        api_key = decrypt_api_key(api_key_record.key_encrypted)

        # Get provider info
        provider = db.query(Provider).filter(Provider.id == job.provider_id).first()
        if not provider:
            job.status = "failed"
            job.error_details = "Provider not found"
            job.finished_at = datetime.now()
            db.commit()
            return

        # Get provider adapter
        try:
            adapter = provider_registry.get_adapter(provider.name)
        except ValueError as e:
            job.status = "failed"
            job.error_details = str(e)
            job.finished_at = datetime.now()
            db.commit()
            return

        # Build options from requested range
        options = {}
        if job.requested_range:
            options = dict(job.requested_range)

        # Import conversations
        conversations_count = 0
        messages_count = 0
        artifacts_count = 0
        errors = []

        try:
            # List conversations
            conv_summaries = await adapter.list_conversations(api_key, options)

            for summary in conv_summaries:
                try:
                    # Fetch full conversation
                    conv_detail = await adapter.fetch_conversation(
                        api_key,
                        summary.provider_conversation_id
                    )

                    # Check if conversation already exists
                    existing = db.query(Conversation).filter(
                        Conversation.provider_id == provider.id,
                        Conversation.provider_conversation_id == conv_detail.provider_conversation_id
                    ).first()

                    if existing:
                        # Skip duplicate
                        continue

                    # Create conversation
                    conversation = Conversation(
                        provider_id=provider.id,
                        provider_conversation_id=conv_detail.provider_conversation_id,
                        title=conv_detail.title,
                        started_at=conv_detail.started_at,
                        ended_at=conv_detail.ended_at,
                        import_job_id=job.id,
                        raw_metadata=conv_detail.raw_metadata
                    )
                    db.add(conversation)
                    db.flush()  # Get conversation ID

                    conversations_count += 1

                    # Import messages
                    for msg in conv_detail.messages:
                        message = Message(
                            conversation_id=conversation.id,
                            provider_message_id=msg.provider_message_id,
                            role=msg.role,
                            content=msg.content,
                            created_at=msg.created_at,
                            sequence_index=msg.sequence_index,
                            raw_metadata=msg.raw_metadata
                        )
                        db.add(message)
                        messages_count += 1

                    # Import artifacts
                    for art in conv_detail.artifacts:
                        artifact = Artifact(
                            conversation_id=conversation.id,
                            artifact_type=art.artifact_type,
                            provider_artifact_id=art.provider_artifact_id,
                            filename=art.filename,
                            mime_type=art.mime_type,
                            download_status=art.download_status,
                            download_error=art.download_error,
                            raw_metadata=art.raw_metadata
                        )
                        db.add(artifact)
                        artifacts_count += 1

                    db.commit()

                except Exception as e:
                    errors.append(f"Error importing conversation {summary.provider_conversation_id}: {str(e)}")
                    db.rollback()
                    continue

            # Update job status
            job.status = "success" if not errors else "partial"
            job.conversations_imported = conversations_count
            job.messages_imported = messages_count
            job.artifacts_imported = artifacts_count
            job.summary = f"Imported {conversations_count} conversations, {messages_count} messages, {artifacts_count} artifacts"
            if errors:
                job.error_details = "\n".join(errors[:10])  # Limit error details
            job.finished_at = datetime.now()

            # Update API key last used
            api_key_record.last_used_at = datetime.now()

            db.commit()

        except Exception as e:
            job.status = "failed"
            job.error_details = str(e)
            job.finished_at = datetime.now()
            db.commit()

    finally:
        db.close()


@router.get("", response_model=List[ImportJobResponse])
def list_import_jobs(
    provider_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """List import jobs with optional provider filter."""
    query = db.query(ImportJob)

    if provider_id:
        query = query.filter(ImportJob.provider_id == provider_id)

    jobs = query.order_by(ImportJob.started_at.desc()).all()
    return jobs


@router.get("/{job_id}", response_model=ImportJobResponse)
def get_import_job(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific import job."""
    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    return job


@router.post("", response_model=ImportJobResponse)
def create_import_job(
    job_data: ImportJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create and start a new import job.

    The job will run in the background and import conversations from the provider.
    """
    # Verify API key exists and is active
    api_key = db.query(APIKey).filter(APIKey.id == job_data.api_key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    if not api_key.is_active:
        raise HTTPException(status_code=400, detail="API key is not active")

    # Verify provider exists
    provider = db.query(Provider).filter(Provider.id == job_data.provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Create requested range
    requested_range = {}
    if job_data.from_date:
        requested_range["from_date"] = job_data.from_date.isoformat()
    if job_data.to_date:
        requested_range["to_date"] = job_data.to_date.isoformat()

    # Create import job
    job = ImportJob(
        provider_id=job_data.provider_id,
        api_key_id=job_data.api_key_id,
        status="running",
        requested_range=requested_range if requested_range else None
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Start background task
    from ..config import get_settings
    settings = get_settings()
    background_tasks.add_task(run_import_job, job.id, settings.database_url)

    return job
