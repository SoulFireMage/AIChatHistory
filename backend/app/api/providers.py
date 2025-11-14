from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Provider
from .schemas import ProviderResponse

router = APIRouter()


@router.get("", response_model=List[ProviderResponse])
def list_providers(db: Session = Depends(get_db)):
    """List all available providers."""
    providers = db.query(Provider).all()
    return providers
