"""AI-ассистент «эксперт-пивовар»: разбор отклонений в отчёте."""
import logging
from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.config import settings
from app.crud import report as crud_report
from app.models import User
from app.auth.auth import get_current_active_user
from app.services import ai_analysis

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/analytics/summary")
def analytics_summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    template_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Сводная аналитика отклонений по отчётам за период (в норме/отклонения, по дням,
    по шаблонам, топ показателей, список отклонений)."""
    return ai_analysis.build_period_analytics(db, date_from=date_from, date_to=date_to, template_id=template_id)


@router.post("/analytics/analyze")
def analytics_analyze(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    template_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Нарратив-отчёт эксперта по отклонениям за период (нужна подключённая модель)."""
    if not settings.ai_enabled:
        raise HTTPException(status_code=404, detail="Модуль AI-ассистента отключён")
    analytics = ai_analysis.build_period_analytics(db, date_from=date_from, date_to=date_to, template_id=template_id)
    from app.services import ai_agent
    try:
        result = ai_agent.run_period_agent(db, analytics)
    except Exception as e:
        logger.exception("Агентный разбор периода не удался")
        raise HTTPException(status_code=502, detail=f"Ошибка агента: {e}")
    if not result.get("model_configured"):
        raise HTTPException(
            status_code=409,
            detail="Модель не подключена. Задайте OPENROUTER_API_KEY (или ANTHROPIC_API_KEY).",
        )
    return {**analytics, "summary": result.get("text", ""), "tool_calls": result.get("tool_calls", 0)}


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

    # Заземление на техкарту сорта из базы знаний (RAG). Необязательно:
    # если модуль RAG недоступен или ничего не нашлось — разбор идёт без него.
    knowledge = _retrieve_knowledge(db, ctx, deviations)

    provider = ai_analysis.get_provider()
    try:
        result = provider.analyze(ctx, deviations, knowledge=knowledge)
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
        "knowledge_used": len(knowledge),
        "summary": result.get("summary", ""),
        "deviations": result.get("deviations", []),
    }


@router.post("/chat")
def agent_chat(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Чат с агентом: он сам смотрит анализы (за дату/период/партию), техкарты и внешние
    источники и отвечает. Тело: {message: str, history: [{role, content}]}."""
    if not settings.ai_enabled:
        raise HTTPException(status_code=404, detail="Модуль AI-ассистента отключён")
    message = (payload.get("message") or "").strip()
    history = payload.get("history") or []
    if not message:
        raise HTTPException(status_code=400, detail="Пустой вопрос")
    history = [m for m in history if isinstance(m, dict)] + [{"role": "user", "content": message}]

    from app.services import ai_agent
    try:
        result = ai_agent.run_chat_agent(db, history)
    except Exception as e:
        logger.exception("Чат-агент не удался")
        raise HTTPException(status_code=502, detail=f"Ошибка агента: {e}")
    if not result.get("model_configured"):
        raise HTTPException(
            status_code=409,
            detail="Модель не подключена. Задайте OPENROUTER_API_KEY (или ANTHROPIC_API_KEY).",
        )
    return {"text": result.get("text", "")}


@router.post("/reports/{report_id}/agent")
def agent_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Агентный разбор отчёта на харнессе Tool Runner: модель сама решает, что искать —
    во внутренних техкартах (RAG) и во внешних источниках (веб-поиск) — и даёт
    рекомендации по отклонениям. Нужна подключённая модель (ANTHROPIC_API_KEY)."""
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
            "model_configured": True,
            "text": "Все показатели в пределах норм — отклонений не обнаружено.",
            "deviations": [],
        }

    from app.services import ai_agent
    try:
        result = ai_agent.run_brewing_agent(db, ctx, deviations, variety=ctx.get("variety"))
    except Exception as e:
        logger.exception("Агентный разбор отчёта %s не удался", report_id)
        raise HTTPException(status_code=502, detail=f"Ошибка агента: {e}")

    if not result.get("model_configured"):
        raise HTTPException(
            status_code=409,
            detail="Модель не подключена. Задайте OPENROUTER_API_KEY (или ANTHROPIC_API_KEY), чтобы включить агента с внешними источниками.",
        )

    return {
        "deviations_count": len(deviations),
        "model_configured": True,
        "tool_calls": result.get("tool_calls", 0),
        "text": result.get("text", ""),
        "deviations": deviations,
    }


def _retrieve_knowledge(db: Session, ctx: dict, deviations: list) -> list:
    """Найти релевантные фрагменты техкарты сорта под текущие отклонения."""
    try:
        from app.services import rag
    except Exception:
        return []
    # запрос: сорт + названия отклонившихся показателей
    terms = [d["indicator"] for d in deviations]
    variety = ctx.get("variety")
    query = " ".join(([variety] if variety else []) + terms).strip()
    if not query:
        return []
    try:
        return rag.search_chunks(db, query, variety=variety, limit=5)
    except Exception:
        logger.warning("RAG-поиск недоступен, разбор без техкарты", exc_info=True)
        return []
