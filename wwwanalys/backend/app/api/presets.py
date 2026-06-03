"""Presets API endpoints."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import preset as crud
from app.models import User
from app.schemas.preset import Preset as PresetSchema, PresetCreate, PresetListItem
from app.auth.auth import get_current_admin_user

router = APIRouter()


def _format_preset(preset):
    """Форматирует пресет с обогащением показателей данными из справочника."""
    indicators = []
    for pi in preset.indicators:
        ind_ref = pi.indicator_ref
        options = None
        if ind_ref and ind_ref.options:
            import json
            try:
                options = json.loads(ind_ref.options)
            except (json.JSONDecodeError, TypeError):
                options = None

        indicators.append({
            "id": pi.id,
            "preset_id": pi.preset_id,
            "indicator_id": pi.indicator_id,
            "min_value": pi.min_value,
            "max_value": pi.max_value,
            "sort_order": pi.sort_order,
            "is_required": bool(pi.is_required),
            "indicator_name": ind_ref.name if ind_ref else "",
            "indicator_unit": ind_ref.unit if ind_ref else "",
            "indicator_data_type": ind_ref.data_type if ind_ref else "number",
            "indicator_options": options,
        })

    return {
        "id": preset.id,
        "name": preset.name,
        "description": preset.description,
        "category": preset.category,
        "created_at": preset.created_at,
        "created_by": preset.created_by,
        "indicators": indicators,
    }


@router.get("/", response_model=List[PresetListItem])
def get_presets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить список пресетов (админ)."""
    presets = crud.get_presets(db, skip=skip, limit=limit, category=category)
    result = []
    for p in presets:
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "category": p.category,
            "indicators_count": len(p.indicators),
            "created_at": p.created_at,
        })
    return result


@router.get("/count")
def get_presets_count(
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить количество пресетов."""
    count = crud.get_presets_count(db, category=category)
    return {"count": count}


@router.get("/{preset_id}", response_model=PresetSchema)
def get_preset(
    preset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить пресет по ID (админ)."""
    preset = crud.get_preset(db, preset_id=preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return _format_preset(preset)


@router.post("/", response_model=PresetSchema)
def create_preset(
    preset: PresetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Создать новый пресет (админ)."""
    db_preset = crud.create_preset(db, preset, user_id=current_user.id)
    return _format_preset(db_preset)


@router.delete("/{preset_id}")
def delete_preset(
    preset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Удалить пресет (админ)."""
    db_preset = crud.delete_preset(db, preset_id=preset_id)
    if not db_preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return {"message": "Preset deleted successfully"}