"""AI-ассистент «эксперт-пивовар»: разбор отклонений в отчёте."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.config import settings
from app.crud import report as crud_report
from app.models import User
from app.auth.auth import get_current_active_user
from app.services import ai_analysis

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
def ai_status(current_user: User = Depends(get_current_active_user)):
    """Доступность модуля Агента для интерфейса.

    enabled — модуль включён; model_configured — подключена ли экспертная модель
    (иначе разбор работает в режиме «только факты»).
    """
    if not settings.ai_enabled:
        return {"enabled": False, "provider": None, "model_configured": False}
    provider = ai_analysis.get_provider()
    return {
        "enabled": True,
        "provider": provider.name,
        "model_configured": provider.name != "none",
    }


@router.post("/reports/{report_id}/analyze")
def analyze_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Разобрать отклонения показателей отчёта.

    Движок отклонений работает всегда (без модели). Если подключена экспертная
    модель — добавляется текстовый разбор (трактовка, причины, действия).
    Возвращает {deviations_count, model, summary, deviations:[...]}.
    """
    if not settings.ai_enabled:
        raise HTTPException(status_code=404, detail="Модуль AI-ассистента отключён")

    report = crud_report.get_report(db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")

    ctx = ai_analysis.build_report_context(db, report)
    deviations = ai_analysis.compute_deviations(ctx["values"])

    if not deviations:
        return {
            "deviations_count": 0,
            "model": None,
            "summary": "Все показатели в пределах норм — отклонений не обнаружено.",
            "deviations": [],
        }

    provider = ai_analysis.get_provider()
    try:
        result = provider.analyze(ctx, deviations)
    except Exception as e:
        logger.exception("AI-разбор отчёта %s (провайдер %s) не удался", report_id, provider.name)
        raise HTTPException(status_code=502, detail=f"Ошибка экспертного слоя: {e}")

    # Дополняем ответ факты-числами из движка (по названию показателя)
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
        "model": provider.name,
        "summary": result.get("summary", ""),
        "deviations": result.get("deviations", []),
    }
