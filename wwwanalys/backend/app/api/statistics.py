"""Statistics API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.core.deps import get_db
from app.auth.auth import get_current_active_user
from app.models import User, IndicatorLibrary, TemplateIndicator, IndicatorValue, ProcessLog, AnalysisType

router = APIRouter()


@router.get("/indicators/stats")
def get_indicator_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить статистику использования показателей."""
    total_indicators = db.query(func.count(IndicatorLibrary.id)).scalar() or 0
    total_templates = db.query(func.count(AnalysisType.id)).scalar() or 0
    total_values = db.query(func.count(IndicatorValue.id)).scalar() or 0
    total_processes = db.query(func.count(ProcessLog.id)).scalar() or 0

    # Показатели по категориям
    category_counts = db.query(
        IndicatorLibrary.category,
        func.count(IndicatorLibrary.id)
    ).group_by(IndicatorLibrary.category).all()

    # Показатели по типам данных
    type_counts = db.query(
        IndicatorLibrary.data_type,
        func.count(IndicatorLibrary.id)
    ).group_by(IndicatorLibrary.data_type).all()

    # Самые используемые показатели (по количеству использований в шаблонах)
    most_used = db.query(
        IndicatorLibrary.id,
        IndicatorLibrary.name,
        IndicatorLibrary.unit,
        func.count(TemplateIndicator.id).label('usage_count')
    ).join(
        TemplateIndicator,
        IndicatorLibrary.id == TemplateIndicator.indicator_id
    ).group_by(
        IndicatorLibrary.id, IndicatorLibrary.name, IndicatorLibrary.unit
    ).order_by(
        func.count(TemplateIndicator.id).desc()
    ).limit(10).all()

    # Обязательные vs необязательные
    required_count = db.query(func.count(IndicatorLibrary.id)).filter(
        IndicatorLibrary.is_required == True
    ).scalar() or 0

    # Показатели без категории
    no_category = db.query(func.count(IndicatorLibrary.id)).filter(
        IndicatorLibrary.category.is_(None)
    ).scalar() or 0

    return {
        "total_indicators": total_indicators,
        "total_templates": total_templates,
        "total_values": total_values,
        "total_processes": total_processes,
        "by_category": [{"category": cat, "count": cnt} for cat, cnt in category_counts if cat],
        "by_type": [{"data_type": t, "count": cnt} for t, cnt in type_counts],
        "most_used": [
            {"id": id_, "name": name, "unit": unit, "usage_count": cnt}
            for id_, name, unit, cnt in most_used
        ],
        "required_count": required_count,
        "no_category_count": no_category,
    }