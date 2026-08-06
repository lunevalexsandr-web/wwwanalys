"""Reports API endpoints."""
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import report as crud_report
from app.models import User, PlanItem
from app.schemas import ReportCreate, Report
from app.auth.auth import get_current_active_user

router = APIRouter()


@router.post("/")
def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new report with indicator values (for all authenticated users)."""
    db_report = crud_report.create_report(db=db, report=report, user_id=current_user.id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Если отчет создан из элемента плана - обновляем связь
    if report.plan_item_id:
        plan_item = db.query(PlanItem).filter(PlanItem.id == report.plan_item_id).first()
        if plan_item:
            plan_item.completed_report_id = db_report.id
            plan_item.is_completed = True
            db.commit()
    
    return {
        "id": db_report.id,
        "batch_number": db_report.batch_number,
        "variety": db_report.variety,
        "container": db_report.container,
        "analysis_type_id": db_report.analysis_type_id,
        "started_at": db_report.started_at,
        "status": db_report.status.value if hasattr(db_report.status, 'value') else db_report.status,
        "notes": db_report.notes,
        "values": []
    }


@router.put("/{report_id}")
def update_report(
    report_id: int,
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing report."""
    db_report = crud_report.get_report(db, report_id=report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check permissions for non-admin users
    if not current_user.is_admin and db_report.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update report
    updated_report = crud_report.update_report(db=db, report_id=report_id, report=report)
    if not updated_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {
        "id": updated_report.id,
        "batch_number": updated_report.batch_number,
        "variety": updated_report.variety,
        "container": updated_report.container,
        "analysis_type_id": updated_report.analysis_type_id,
        "started_at": updated_report.started_at,
        "status": updated_report.status.value if hasattr(updated_report.status, 'value') else updated_report.status,
        "notes": updated_report.notes,
        "values": []
    }


@router.get("/", response_model=List[Report])
def get_reports(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get reports list (for all authenticated users)."""
    if current_user.is_admin:
        reports = crud_report.get_reports(db, skip=skip, limit=limit)
    else:
        reports = crud_report.get_reports_by_user(db, user_id=current_user.id)
    return reports


@router.get("/filtered/list", response_model=List[Report])
def get_reports_filtered(
    template_id: Optional[int] = Query(None, description="Filter by template ID"),
    date_from: Optional[date] = Query(None, description="Start date (format: YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (format: YYYY-MM-DD)"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get reports with filtering by template and date (for all authenticated users)."""
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


@router.get("/template/{template_id}", response_model=List[Report])
def get_reports_by_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get reports by template (for all authenticated users)."""
    reports = crud_report.get_reports_by_template(db, template_id=template_id)
    return reports


@router.delete("/history/clear")
def clear_reports_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Clear all user's report history."""
    result = crud_report.delete_all_reports_by_user(db, user_id=current_user.id)
    return result


@router.get("/{report_id}")
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific report (for all authenticated users)."""
    db_report = crud_report.get_report(db, report_id=report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check permissions for non-admin users
    if not current_user.is_admin and db_report.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    from app.schemas.report import IndicatorValueReport
    from app.models import IndicatorLibrary, TemplateIndicator
    
    # Получаем все значения показателей для отчета
    indicator_values = []
    if hasattr(db_report, 'indicator_values') and db_report.indicator_values:
        for v in db_report.indicator_values:
            # Ищем показатель в справочнике
            lib_indicator = db.query(IndicatorLibrary).filter(IndicatorLibrary.id == v.indicator_id).first()
            
            # Получаем название и единицу измерения из справочника
            name = lib_indicator.name if lib_indicator else f"Показатель #{v.indicator_id}"
            unit = lib_indicator.unit if lib_indicator else ""
            
            # Норма: сначала из матрицы (день+тара), фолбэк на TemplateIndicator
            from app.services.norms import resolve_norm
            min_value = max_value = norm_text = None
            norm = resolve_norm(
                db, db_report.analysis_type_id, v.indicator_id,
                day=getattr(v, "day", None), container=getattr(db_report, "container", None),
            )
            if norm is not None:
                min_value, max_value, norm_text = norm.min_value, norm.max_value, norm.norm_text
            if min_value is None and max_value is None and not norm_text:
                template_indicator = db.query(TemplateIndicator).filter(
                    TemplateIndicator.indicator_id == v.indicator_id,
                    TemplateIndicator.template_id == db_report.analysis_type_id
                ).first()
                if template_indicator:
                    min_value = template_indicator.min_value
                    max_value = template_indicator.max_value
                    norm_text = template_indicator.norm_text

            indicator_values.append({
                "id": v.id,
                "indicator_id": v.indicator_id,
                "name": name,
                "unit": unit,
                "value": v.value,
                "text_value": v.text_value,
                "day": getattr(v, "day", None),
                "is_normal": v.is_normal,
                "min_value": min_value,
                "max_value": max_value,
                "norm_text": norm_text
            })
    
    return {
        "id": db_report.id,
        "batch_number": db_report.batch_number,
        "variety": getattr(db_report, "variety", None),
        "container": getattr(db_report, "container", None),
        "analysis_type_id": db_report.analysis_type_id,
        "started_at": db_report.started_at,
        "status": db_report.status.value if hasattr(db_report.status, 'value') else db_report.status,
        "notes": db_report.notes,
        "created_by": db_report.created_by,
        "indicator_values": indicator_values,
        "values": indicator_values
    }