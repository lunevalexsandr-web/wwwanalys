from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models import Preset, PresetIndicator, IndicatorLibrary
from app.schemas.preset import PresetCreate, PresetIndicatorCreate
from typing import List, Optional


def get_presets(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
) -> List[Preset]:
    """Получить список пресетов с возможностью фильтрации по категории."""
    query = db.query(Preset).options(
        joinedload(Preset.indicators).joinedload(PresetIndicator.indicator_ref)
    )
    if category:
        query = query.filter(Preset.category == category)
    return query.order_by(Preset.name).offset(skip).limit(limit).all()


def get_presets_count(db: Session, category: Optional[str] = None) -> int:
    """Получить количество пресетов."""
    query = db.query(func.count(Preset.id))
    if category:
        query = query.filter(Preset.category == category)
    return query.scalar()


def get_preset(db: Session, preset_id: int) -> Optional[Preset]:
    """Получить пресет по ID с показателями."""
    return db.query(Preset).options(
        joinedload(Preset.indicators).joinedload(PresetIndicator.indicator_ref)
    ).filter(Preset.id == preset_id).first()


def create_preset(db: Session, preset: PresetCreate, user_id: int) -> Preset:
    """Создать новый пресет."""
    db_preset = Preset(
        name=preset.name,
        description=preset.description,
        category=preset.category,
        created_by=user_id,
    )
    db.add(db_preset)
    db.flush()

    # Добавляем показатели
    for ind_data in preset.indicators:
        db_pi = PresetIndicator(
            preset_id=db_preset.id,
            indicator_id=ind_data.indicator_id,
            min_value=ind_data.min_value,
            max_value=ind_data.max_value,
            sort_order=ind_data.sort_order or 0,
            is_required=1 if ind_data.is_required else 0,
        )
        db.add(db_pi)

    db.commit()
    db.refresh(db_preset)
    # Перезагружаем с joinedload
    return get_preset(db, db_preset.id)


def delete_preset(db: Session, preset_id: int) -> Optional[Preset]:
    """Удалить пресет."""
    db_preset = db.query(Preset).filter(Preset.id == preset_id).first()
    if db_preset:
        db.delete(db_preset)
        db.commit()
    return db_preset


def create_template_from_preset(
    db: Session,
    preset_id: int,
    template_name: str,
    template_description: str,
    user_id: int,
) -> Optional[Preset]:
    """Применить пресет: на его основе создаётся AnalysisType."""
    from app.models import AnalysisType, TemplateIndicator

    db_preset = get_preset(db, preset_id)
    if not db_preset:
        return None

    # Создаём шаблон типа 'pure' — только из справочника
    db_template = AnalysisType(
        name=template_name,
        description=template_description or db_preset.description,
        created_by=user_id,
        is_active=True,
        template_type='pure',  # Пресет даёт только библиотечные показатели
    )
    db.add(db_template)
    db.flush()

    # Добавляем показатели из пресета как TemplateIndicator
    for pi in db_preset.indicators:
        ti = TemplateIndicator(
            template_id=db_template.id,
            indicator_id=pi.indicator_id,
            min_value=pi.min_value,
            max_value=pi.max_value,
            sort_order=pi.sort_order,
            is_custom=False,
        )
        db.add(ti)

    db.commit()
    db.refresh(db_template)
    return db_template