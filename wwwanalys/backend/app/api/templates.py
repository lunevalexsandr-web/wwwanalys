from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import SessionLocal
from app.crud import analysis_type as crud_template
from app.crud import user as crud_user
from app.models import User
from app.schemas import AnalysisType, AnalysisTypeCreate, AnalysisTypeUpdate
from app.auth.auth import get_current_active_user, get_current_admin_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[AnalysisType])
def get_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить список всех шаблонов (только для Admin)"""
    templates = crud_template.get_templates(db, skip=skip, limit=limit)
    return templates

@router.post("/", response_model=AnalysisType)
def create_template(
    template: AnalysisTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Создать новый шаблон с индикаторами (только для Admin)"""
    db_template = crud_template.create_template(db=db, template=template, user_id=current_user.id)
    return db_template

@router.get("/active", response_model=List[AnalysisType])
def get_active_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить список активных шаблонов (для Admin и User)"""
    templates = crud_template.get_active_templates(db)
    return templates

@router.get("/{template_id}", response_model=AnalysisType)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить конкретный шаблон (только для Admin)"""
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
    """Обновить шаблон (только для Admin)"""
    db_template = crud_template.update_template(db, template_id=template_id, template=template)
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template

@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Удалить шаблон (только для Admin)"""
    db_template = crud_template.delete_template(db, template_id=template_id)
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted successfully"}
