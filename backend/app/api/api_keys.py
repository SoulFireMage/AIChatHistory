from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..models import APIKey, Provider
from ..services import encrypt_api_key
from .schemas import APIKeyCreate, APIKeyResponse, APIKeyUpdate

router = APIRouter()


@router.get("", response_model=List[APIKeyResponse])
def list_api_keys(db: Session = Depends(get_db)):
    """List all API keys (without exposing actual key values)."""
    api_keys = db.query(APIKey).all()
    return api_keys


@router.post("", response_model=APIKeyResponse)
def create_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db)
):
    """Create a new API key."""
    # Verify provider exists
    provider = db.query(Provider).filter(Provider.id == api_key_data.provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Encrypt the API key
    encrypted_key = encrypt_api_key(api_key_data.api_key_value)

    # Create the API key record
    api_key = APIKey(
        provider_id=api_key_data.provider_id,
        label=api_key_data.label,
        key_encrypted=encrypted_key
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return api_key


@router.patch("/{api_key_id}", response_model=APIKeyResponse)
def update_api_key(
    api_key_id: UUID,
    update_data: APIKeyUpdate,
    db: Session = Depends(get_db)
):
    """Update an API key (label or active status)."""
    api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    if update_data.label is not None:
        api_key.label = update_data.label
    if update_data.is_active is not None:
        api_key.is_active = update_data.is_active

    db.commit()
    db.refresh(api_key)

    return api_key


@router.delete("/{api_key_id}")
def delete_api_key(
    api_key_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete an API key."""
    api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    db.delete(api_key)
    db.commit()

    return {"message": "API key deleted successfully"}
