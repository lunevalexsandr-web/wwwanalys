"""Templates API endpoints."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import analysis_type as crud_template
from app.models import User
from app.schemas import AnalysisType, AnalysisTypeCreate, AnalysisTypeUpdate
from app.auth.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


@router.get("/", response_model=List[AnalysisType])
def get_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all templates (admin only)."""
    templates = crud_template.get_templates(db, skip=skip, limit=limit)
    return templates


@router.post("/", response_model=AnalysisType)
def create_template(
    template: AnalysisTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new template with indicators (admin only)."""
    db_template = crud_template.create_template(db=db, template=template, user_id=current_user.id)
    return db_template


@router.get("/active", response_model=List[AnalysisType])
def get_active_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get active templates (for all authenticated users)."""
    templates = crud_template.get_active_templates(db)
    return templates


@router.get("/{template_id}", response_model=AnalysisType)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get a specific template (admin only)."""
    db_template = crud_template.get_analysis_type(db, analysis_type_id=template_id)
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template


@router.put("/{template_id}", response_model=AnalysisType)
def update_template(
    template_id: int,
    template: AnalysisTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a template (admin only)."""
    db_template = crud_template.update_template(db, template_id=template_id, template=template)
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template


@router.delete("/clear-all")
def clear_all_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete all templates (admin only)."""
    count = crud_template.clear_all_templates(db)
    return {"message": f"Удалено шаблонов: {count}", "deleted_count": count}


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a template (admin only)."""
    db_template = crud_template.delete_template(db, template_id=template_id)
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted successfully"}