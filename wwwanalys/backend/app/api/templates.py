"""Templates API endpoints."""
from typing import List
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import analysis_type as crud_template
from app.crud import preset as crud_preset
from app.models import User
from app.schemas import AnalysisType, AnalysisTypeCreate, AnalysisTypeUpdate
from app.schemas.analysis_type import CopyTemplateRequest, CreateFromPresetRequest
from app.auth.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


def _format_template(template, db: Session):
    """Форматирует шаблон с обогащением template_indicators данными из справочника."""
    # Pydantic v2 не умеет автоматически сериализовать вложенные relationship,
    # поэтому формируем template_indicators вручную
    ti_list = []
    
    # Если template_indicators не загружены, пробуем загрузить их вручную
    if not hasattr(template, 'template_indicators') or template.template_indicators is None:
        # Загружаем template_indicators с joinedload
        from sqlalchemy.orm import joinedload
        from app.models import TemplateIndicator
        
        # Это временный обходной путь - в идеале нужно исправить загрузку в CRUD
        db_template = db.query(AnalysisType).options(
            joinedload(AnalysisType.template_indicators).joinedload(TemplateIndicator.indicator_ref)
        ).filter(AnalysisType.id == template.id).first()
        
        if db_template and db_template.template_indicators:
            template_indicators = db_template.template_indicators
        else:
            template_indicators = []
    else:
        template_indicators = template.template_indicators or []
    
    from app.services.norms import get_schedule_days
    for ti in template_indicators:
        lib_ind = ti.indicator_ref
        days = get_schedule_days(db, ti.template_id, ti.indicator_id)
        if lib_ind:
            # Парсим options из JSON
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
                "norm_text": ti.norm_text,
                "days": days,
                "sort_order": ti.sort_order or 0,
                "is_custom": ti.is_custom if ti.is_custom is not None else False,
                "template_notes": ti.template_notes,
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
                "norm_text": ti.norm_text,
                "days": days,
                "sort_order": ti.sort_order or 0,
                "is_custom": ti.is_custom if ti.is_custom is not None else False,
                "template_notes": ti.template_notes,
            })

    return ti_list


def _make_template_response(template, db: Session):
    """Сформировать ответ шаблона через Pydantic модели."""
    from app.schemas.analysis_type import AnalysisType as AnalysisTypeSchema
    
    # объекты отбора, встречающиеся в нормах шаблона (для выбора в отчёте)
    from app.models import TemplateNorm
    obj_rows = (
        db.query(TemplateNorm.object_key, TemplateNorm.object_name)
        .filter(TemplateNorm.template_id == template.id, TemplateNorm.object_key.isnot(None))
        .distinct()
        .all()
    )
    objects = [
        {"key": k, "name": n or k}
        for k, n in sorted(obj_rows, key=lambda x: (x[1] or ""))
    ]

    template_dict = {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "created_at": template.created_at,
        "created_by": template.created_by,
        "is_active": template.is_active,
        "indicators": template.indicators,
        "template_indicators": _format_template(template, db),
        "objects": objects,
    }
    
    # Используем model_validate для корректной сериализации в Pydantic v2
    return AnalysisTypeSchema.model_validate(template_dict)


@router.get("/", response_model=List[AnalysisType])
def get_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all templates (admin only)."""
    templates = crud_template.get_templates(db, skip=skip, limit=limit)
    
    # Обогащаем template_indicators
    result = []
    for t in templates:
        result.append(_make_template_response(t, db))
    
    return result


@router.post("/", response_model=AnalysisType)
def create_template(
    template: AnalysisTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new template with indicators (admin only)."""
    db_template = crud_template.create_template(db=db, template=template, user_id=current_user.id)
    return _make_template_response(db_template, db)


@router.get("/active", response_model=List[AnalysisType])
def get_active_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get active templates (for all authenticated users)."""
    templates = crud_template.get_active_templates(db)
    
    result = []
    for t in templates:
        result.append(_make_template_response(t, db))
    
    return result


@router.get("/{template_id}/norms")
def get_template_norms(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Матрица норм шаблона: по каждому показателю — нормы с разбивкой по
    сорту / объекту отбора / таре / дню (для проверки зависимостей)."""
    from app.models import TemplateNorm, IndicatorLibrary, Variety
    rows = (
        db.query(TemplateNorm)
        .filter(TemplateNorm.template_id == template_id)
        .all()
    )
    ind_names = {i.id: i.name for i in db.query(IndicatorLibrary).all()}
    var_names = {str(v.external_id).lower(): v.name for v in db.query(Variety).all() if v.external_id}
    out = []
    for r in rows:
        out.append({
            "indicator": ind_names.get(r.indicator_id, f"#{r.indicator_id}"),
            "indicator_id": r.indicator_id,
            "day": r.day,
            "variety": var_names.get(str(r.variety_key).lower()) if r.variety_key else None,
            "variety_key": r.variety_key,
            "container": r.container,
            "object": r.object_name or r.object_key,
            "min_value": r.min_value,
            "max_value": r.max_value,
            "norm_text": r.norm_text,
        })
    out.sort(key=lambda x: (x["indicator"], x["day"] if x["day"] is not None else -1,
                            x["variety"] or "", x["object"] or "", x["container"] or ""))
    return out


@router.get("/{template_id}", response_model=AnalysisType)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific template (available to all authenticated users)."""
    db_template = crud_template.get_analysis_type(db, analysis_type_id=template_id)
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return _make_template_response(db_template, db)


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
    
    return _make_template_response(db_template, db)


@router.post("/{template_id}/copy", response_model=AnalysisType)
def copy_template(
    template_id: int,
    request: CopyTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Copy a template with a new name (admin only)."""
    db_template = crud_template.copy_template(
        db,
        template_id=template_id,
        new_name=request.new_name,
        new_description=request.new_description or "",
        user_id=current_user.id,
    )
    return _make_template_response(db_template, db)


@router.post("/from-preset", response_model=AnalysisType)
def create_template_from_preset(
    request: CreateFromPresetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a template from a preset (admin only)."""
    db_template = crud_preset.create_template_from_preset(
        db,
        preset_id=request.preset_id,
        template_name=request.template_name,
        template_description=request.template_description or "",
        user_id=current_user.id,
    )
    if not db_template:
        raise HTTPException(status_code=404, detail="Preset not found")
    return _make_template_response(db_template, db)


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