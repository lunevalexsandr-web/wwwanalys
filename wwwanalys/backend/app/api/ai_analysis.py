"""AI-ассистент «эксперт-пивовар»: разбор отклонений в отчёте."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import report as crud_report
from app.models import User
from app.auth.auth import get_current_active_user
from app.services import ai_analysis

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/reports/{report_id}/analyze")
def analyze_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Разобрать отклонения показателей отчёта с помощью ИИ-эксперта.

    Возвращает {deviations_count, summary, deviations:[...]}.
    Если отклонений нет — summary с сообщением и пустой список.
    """
    if not ai_analysis.is_ai_configured():
        raise HTTPException(
            status_code=503,
            detail="AI-ассистент не настроен: не задан ANTHROPIC_API_KEY на сервере.",
        )

    report = crud_report.get_report(db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")

    ctx = ai_analysis.build_report_context(db, report)
    deviations = ai_analysis.compute_deviations(ctx["values"])

    if not deviations:
        return {
            "deviations_count": 0,
            "summary": "Все показатели в пределах норм — отклонений не обнаружено.",
            "deviations": [],
        }

    try:
        result = ai_analysis.analyze_deviations(ctx, deviations)
    except Exception as e:
        logger.exception("AI-анализ отчёта %s не удался", report_id)
        raise HTTPException(status_code=502, detail=f"Ошибка AI-ассистента: {e}")

    # Дополняем ответ модели фактами-числами из движка (по названию показателя)
    facts = {d["indicator"]: d for d in deviations}
    for item in result.get("deviations", []):
        f = facts.get(item.get("indicator"))
        if f:
            item["value"] = f["value"]
            item["unit"] = f["unit"]
            item["norm"] = f["norm"]
            item["direction"] = f["direction"]
            item["deviation_pct"] = f["deviation_pct"]

    return {
        "deviations_count": len(deviations),
        "summary": result.get("summary", ""),
        "deviations": result.get("deviations", []),
    }
