from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
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

@router.post("/")
def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Создать новый отчет с значениями индикаторов (для Admin и User)"""
    db_report = crud_report.create_report(db=db, report=report, user_id=current_user.id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Template not found")
    return {
        "id": db_report.id,
        "batch_number": db_report.batch_number,
        "analysis_type_id": db_report.analysis_type_id,
        "started_at": db_report.started_at,
        "status": db_report.status.value if hasattr(db_report.status, 'value') else db_report.status,
        "notes": db_report.notes,
        "values": []
    }

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

@router.get("/filtered/list", response_model=List[Report])
def get_reports_filtered(
    template_id: Optional[int] = Query(None, description="Фильтр по ID шаблона"),
    date_from: Optional[date] = Query(None, description="Дата начала (формат: YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Дата окончания (формат: YYYY-MM-DD)"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить отчеты с фильтрацией по шаблону и дате (для Admin и User)"""
    reports = crud_report.get_reports_filtered(
        db, 
        user_id=current_user.id,
        template_id=template_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit
    )
    return reports

@router.delete("/history/clear")
def clear_reports_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Очистить всю историю отчетов пользователя"""
    result = crud_report.delete_all_reports_by_user(db, user_id=current_user.id)
    return result
