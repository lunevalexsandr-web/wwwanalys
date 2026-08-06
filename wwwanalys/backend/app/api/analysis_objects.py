"""Справочник объектов анализа/отбора (только чтение — для проверки)."""
from typing import List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models import User, AnalysisObject
from app.auth.auth import get_current_active_user

router = APIRouter()


class AnalysisObjectOut(BaseModel):
    id: int
    name: str
    external_id: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


@router.get("/", response_model=List[AnalysisObjectOut])
def list_objects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return db.query(AnalysisObject).order_by(AnalysisObject.name).all()
