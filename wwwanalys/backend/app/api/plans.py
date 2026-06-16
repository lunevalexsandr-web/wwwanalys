"""Plans API endpoints."""
from typing import List, Optional
from datetime import date
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import analysis_plan as crud_plan
from app.models import User, AnalysisType, TemplateIndicator, PlanItem
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
    
    # Если template_indicators не загружены, пробуем загрузить их вручную
    if not hasattr(template, 'template_indicators') or template.template_indicators is None:
        from sqlalchemy.orm import joinedload
        from app.models import TemplateIndicator
        db_template = db.query(AnalysisType).options(
            joinedload(AnalysisType.template_indicators).joinedload(TemplateIndicator.indicator_ref)
        ).filter(AnalysisType.id == template.id).first()
        if db_template:
            template_indicators = db_template.template_indicators
        else:
            template_indicators = []
    else:
        template_indicators = template.template_indicators or []
    
    for ti in template_indicators:
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
        else:
            # Если indicator_ref не загружен, создаем минимальную запись
            ti_list.append({
                "id": ti.id,
                "indicator_id": ti.indicator_id,
                "name": f"Показатель #{ti.indicator_id}",
                "unit": "",
                "data_type": "number",
                "options": None,
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
        completed_report_id=item.completed_report_id,
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
    from app.schemas.analysis_plan import AnalysisPlan as AnalysisPlanSchema
    plans = crud_plan.get_plans(db, skip=skip, limit=limit)
    # Форматируем с template_indicators для корректной сериализации Pydantic v2
    return [AnalysisPlanSchema.model_validate(_format_plan_for_response(p, db)) for p in plans]


def _format_plan_for_response(db_plan, db: Session) -> dict:
    """Форматирует план с template_indicators для корректной сериализации в Pydantic v2."""
    from app.schemas.analysis_plan import AnalysisPlan as AnalysisPlanSchema, PlanItemDetail as PlanItemDetailSchema, PlanItemTemplateInfo
    
    plan_items = []
    for item in (db_plan.plan_items or []):
        template_data = None
        if item.template:
            template_indicators = _format_template_indicators(item.template, db)
            template_data = {
                "id": item.template.id,
                "name": item.template.name,
                "description": item.template.description,
                "template_indicators": template_indicators,
            }
        
        plan_items.append({
            "id": item.id,
            "plan_id": item.plan_id,
            "template_id": item.template_id,
            "batch_number": item.batch_number,
            "sort_order": item.sort_order or 0,
            "is_completed": item.is_completed,
            "completed_report_id": item.completed_report_id,
            "template": template_data,
        })
    
    return {
        "id": db_plan.id,
        "name": db_plan.name,
        "description": db_plan.description,
        "plan_date": db_plan.plan_date,
        "created_by": db_plan.created_by,
        "created_at": db_plan.created_at,
        "is_completed": db_plan.is_completed,
        "plan_items": plan_items,
    }


@router.get("/by-date", response_model=List[AnalysisPlan])
def get_plans_by_date(
    plan_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get plans for a specific date."""
    from app.schemas.analysis_plan import AnalysisPlan as AnalysisPlanSchema
    plans = crud_plan.get_plans_by_date(db, plan_date=plan_date)
    # Форматируем вручную для корректной сериализации Pydantic v2
    return [AnalysisPlanSchema.model_validate(_format_plan_for_response(p, db)) for p in plans]


@router.get("/range", response_model=List[AnalysisPlan])
def get_plans_by_range(
    date_from: date,
    date_to: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get plans for a date range."""
    from app.schemas.analysis_plan import AnalysisPlan as AnalysisPlanSchema
    plans = crud_plan.get_plans_by_date_range(db, date_from=date_from, date_to=date_to)
    # Форматируем с template_indicators
    return [AnalysisPlanSchema.model_validate(_format_plan_for_response(p, db)) for p in plans]


@router.post("/", response_model=AnalysisPlan)
def create_plan(
    plan: AnalysisPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new plan (admin only)."""
    db_plan = crud_plan.create_plan(db=db, plan=plan, user_id=current_user.id)
    # После создания загружаем план с template_indicators для корректного ответа
    from app.schemas.analysis_plan import AnalysisPlan as AnalysisPlanSchema
    db_plan_full = crud_plan.get_plan(db, plan_id=db_plan.id)
    if db_plan_full:
        return AnalysisPlanSchema.model_validate(_format_plan_for_response(db_plan_full, db))
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
    from app.schemas.analysis_plan import AnalysisPlan as AnalysisPlanSchema
    return AnalysisPlanSchema.model_validate(_format_plan_for_response(db_plan, db))


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
    from app.schemas.analysis_plan import AnalysisPlan as AnalysisPlanSchema
    # Перезагружаем с template_indicators для корректного ответа
    db_plan_full = crud_plan.get_plan(db, plan_id=plan_id)
    if db_plan_full:
        return AnalysisPlanSchema.model_validate(_format_plan_for_response(db_plan_full, db))
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
    
    # Загружаем template с template_indicators для ответа
    from sqlalchemy.orm import joinedload
    from app.models import TemplateIndicator
    db_item_full = db.query(PlanItem).options(
        joinedload(PlanItem.template).joinedload(AnalysisType.template_indicators).joinedload(TemplateIndicator.indicator_ref)
    ).filter(PlanItem.id == item_id).first()
    
    return _format_plan_item_response(db_item_full, db)