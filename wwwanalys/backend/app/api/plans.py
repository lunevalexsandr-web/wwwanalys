"""Plans API endpoints."""
from typing import List, Optional
from datetime import date
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import analysis_plan as crud_plan
from app.models import User, AnalysisType, TemplateIndicator
from app.schemas import (
    AnalysisPlan,
    AnalysisPlanCreate,
    AnalysisPlanUpdate,
    PlanItemUpdate,
    PlanItemResponse,
)
from app.auth.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


def _format_template_indicators(template: AnalysisType, db: Session) -> List[dict]:
    """Форматирует template_indicators для шаблона в плане."""
    ti_list = []
    for ti in (template.template_indicators or []):
        lib_ind = ti.indicator_ref
        if lib_ind:
            options = None
            if lib_ind.options:
                try:
                    options = json.loads(lib_ind.options)
                except (json.JSONDecodeError, TypeError):
                    options = None

            ti_list.append({
                "id": ti.id,
                "indicator_id": ti.indicator_id,
                "name": lib_ind.name,
                "unit": lib_ind.unit or "",
                "data_type": lib_ind.data_type or "number",
                "options": options,
                "min_value": ti.min_value,
                "max_value": ti.max_value,
                "sort_order": ti.sort_order or 0,
            })
    return ti_list


def _format_plan_item_response(item, db: Session) -> PlanItemResponse:
    """Формирует ответ элемента плана с информацией о шаблоне."""
    template_data = None
    if item.template:
        template_data = {
            "id": item.template.id,
            "name": item.template.name,
            "description": item.template.description,
            "template_indicators": _format_template_indicators(item.template, db),
        }
    
    from app.schemas.analysis_plan import PlanItemResponse as PlanItemResponseSchema
    return PlanItemResponseSchema(
        id=item.id,
        plan_id=item.plan_id,
        template_id=item.template_id,
        batch_number=item.batch_number,
        sort_order=item.sort_order or 0,
        is_completed=item.is_completed,
        template=template_data,
    )


@router.get("/", response_model=List[AnalysisPlan])
def get_plans(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all plans (admin only)."""
    plans = crud_plan.get_plans(db, skip=skip, limit=limit)
    return plans


@router.get("/by-date", response_model=List[AnalysisPlan])
def get_plans_by_date(
    plan_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get plans for a specific date."""
    plans = crud_plan.get_plans_by_date(db, plan_date=plan_date)
    return plans


@router.get("/range", response_model=List[AnalysisPlan])
def get_plans_by_range(
    date_from: date,
    date_to: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get plans for a date range."""
    plans = crud_plan.get_plans_by_date_range(db, date_from=date_from, date_to=date_to)
    return plans


@router.post("/", response_model=AnalysisPlan)
def create_plan(
    plan: AnalysisPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new plan (admin only)."""
    db_plan = crud_plan.create_plan(db=db, plan=plan, user_id=current_user.id)
    return db_plan


@router.get("/{plan_id}", response_model=AnalysisPlan)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific plan."""
    db_plan = crud_plan.get_plan(db, plan_id=plan_id)
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return db_plan


@router.put("/{plan_id}", response_model=AnalysisPlan)
def update_plan(
    plan_id: int,
    plan: AnalysisPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a plan (admin only)."""
    db_plan = crud_plan.update_plan(db, plan_id=plan_id, plan=plan)
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return db_plan


@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a plan (admin only)."""
    db_plan = crud_plan.delete_plan(db, plan_id=plan_id)
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"message": "Plan deleted successfully"}


@router.patch("/items/{item_id}", response_model=PlanItemResponse)
def update_plan_item(
    item_id: int,
    item_update: PlanItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a plan item (mark as completed, etc.)."""
    db_item = crud_plan.update_plan_item(db, item_id=item_id, item_update=item_update)
    if not db_item:
        raise HTTPException(status_code=404, detail="Plan item not found")
    
    # Загружаем template для ответа
    from sqlalchemy.orm import joinedload
    db_item_full = db.query(PlanItem).options(
        joinedload(PlanItem.template)
    ).filter(PlanItem.id == item_id).first()
    
    return _format_plan_item_response(db_item_full, db)