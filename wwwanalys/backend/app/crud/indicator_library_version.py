from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import IndicatorLibrary, IndicatorLibraryVersion
from app.schemas.indicator_library_version import IndicatorLibraryVersionCreate


def get_versions_for_indicator(db: Session, indicator_id: int) -> List[IndicatorLibraryVersion]:
    """Получить все версии изменения показателя."""
    return db.query(IndicatorLibraryVersion)\
        .filter(IndicatorLibraryVersion.indicator_id == indicator_id)\
        .order_by(IndicatorLibraryVersion.version.desc())\
        .all()


def get_latest_version(db: Session, indicator_id: int) -> Optional[IndicatorLibraryVersion]:
    """Получить последнюю версию показателя."""
    return db.query(IndicatorLibraryVersion)\
        .filter(IndicatorLibraryVersion.indicator_id == indicator_id)\
        .order_by(IndicatorLibraryVersion.version.desc())\
        .first()


def create_version(db: Session, version_data: IndicatorLibraryVersionCreate) -> IndicatorLibraryVersion:
    """Создать новую версию показателя."""
    db_version = IndicatorLibraryVersion(**version_data.model_dump())
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version


def create_version_from_indicator(
    db: Session,
    indicator: IndicatorLibrary,
    change_type: str = "update",
    changed_by: Optional[int] = None,
    change_notes: Optional[str] = None
) -> IndicatorLibraryVersion:
    """Создать версию на основе текущего состояния показателя."""
    # Определяем номер версии
    last_version = get_latest_version(db, indicator.id)
    new_version = (last_version.version + 1) if last_version else 1

    version_data = IndicatorLibraryVersionCreate(
        indicator_id=indicator.id,
        version=new_version,
        name=indicator.name,
        unit=indicator.unit or "",
        data_type=indicator.data_type or "number",
        options=indicator.options,
        description=indicator.description,
        category=indicator.category,
        is_required=indicator.is_required or False,
        default_value=indicator.default_value,
        validation_rules=indicator.validation_rules,
        changed_by=changed_by,
        change_type=change_type,
        change_notes=change_notes,
    )
    return create_version(db, version_data)


def delete_versions_for_indicator(db: Session, indicator_id: int) -> int:
    """Удалить все версии показателя."""
    deleted = db.query(IndicatorLibraryVersion)\
        .filter(IndicatorLibraryVersion.indicator_id == indicator_id)\
        .delete()
    db.commit()
    return deleted