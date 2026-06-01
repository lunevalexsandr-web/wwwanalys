from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import SessionLocal
from app.crud import report as crud_report
from app.crud import user as crud_user
from app.models import User
from app.schemas import ReportCreate, Report, IndicatorValueReport
from app.auth.auth import get_current_active_user, get_current_admin_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=Report)
def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Создать новый отчет с значениями индикаторов (для Admin и User)"""
    db_report = crud_report.create_report(db=db, report=report, user_id=current_user.id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_report

@router.get("/", response_model=List[Report])
def get_reports(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить список отчетов (для Admin и User)"""
    if current_user.is_admin:
        reports = crud_report.get_reports(db, skip=skip, limit=limit)
    else:
        reports = crud_report.get_reports_by_user(db, user_id=current_user.id)
    return reports

@router.get("/{report_id}", response_model=Report)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить конкретный отчет (для Admin и User)"""
    db_report = crud_report.get_report(db, report_id=report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Проверка прав доступа для обычных пользователей
    if not current_user.is_admin and db_report.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return db_report

@router.get("/template/{template_id}", response_model=List[Report])
def get_reports_by_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить отчеты по шаблону (для Admin и User)"""
    reports = crud_report.get_reports_by_template(db, template_id=template_id)
    return reports