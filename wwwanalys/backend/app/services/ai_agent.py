"""Агент «эксперт-пивовар» на харнессе Tool Runner (Anthropic SDK).

В отличие от одношагового разбора (ai_analysis.provider.analyze), здесь модель
работает в агентном цикле и сама решает, какие инструменты вызвать:

  • search_tech_cards — RAG-поиск по нашей базе техкарт (внутренние регламенты);
  • web_search       — серверный веб-поиск Anthropic (внешние источники).

Цикл ведёт SDK (client.beta.messages.tool_runner). Модель — claude-opus-4-8.
Активируется только при заданном ANTHROPIC_API_KEY; иначе возвращает
{"model_configured": False}. Числа отклонений считает движок (ai_analysis),
модель их не выдумывает — они передаются в запросе как факты.
"""
import contextvars
import json
import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Контекст текущего запуска агента для инструмента-замыкания (db + сорт).
_agent_ctx: contextvars.ContextVar[dict] = contextvars.ContextVar("agent_ctx")

_AGENT_SYSTEM_PROMPT = (
    "Ты — эксперт-пивовар и технолог лаборатории. Разбираешь отклонения "
    "показателей анализов от норм и даёшь практические рекомендации.\n\n"
    "Инструменты:\n"
    "• search_tech_cards — сначала ищи причины и регламентные требования во "
    "внутренней базе технологических карт предприятия (приоритетный источник).\n"
    "• web_search — затем, при необходимости, уточняй общими знаниями пивоварения "
    "из внешних источников (публикации, стандарты).\n\n"
    "Правила: числовые факты по отклонениям даны в запросе — не изменяй их и не "
    "выдумывай новые. Опирайся в первую очередь на техкарты; если они противоречат "
    "внешним источникам — верь техкарте. Для внешних утверждений указывай источник. "
    "Отвечай на русском, структурно: по каждому отклонению — вероятная причина и "
    "конкретное корректирующее действие; в конце — краткое резюме."
)


def _build_rag_tool():
    """Создать инструмент RAG (декоратор beta_tool) с доступом к БД через contextvar."""
    from anthropic import beta_tool

    @beta_tool
    def search_tech_cards(query: str) -> str:
        """Найти релевантные фрагменты во внутренней базе технологических карт (RAG).

        Используй для причин отклонений и рекомендаций, опирающихся на регламенты
        предприятия. Возвращает выдержки из техкарт.

        Args:
            query: поисковый запрос на русском (показатель, сорт, проблема, процесс).
        """
        ctx = _agent_ctx.get({})
        db = ctx.get("db")
        variety = ctx.get("variety")
        if db is None:
            return "База техкарт недоступна."
        try:
            from app.services.rag import search_chunks
            hits = search_chunks(db, query, variety=variety, limit=5)
        except Exception as e:  # RAG может быть не сконфигурирован
            logger.warning("RAG-поиск в агенте не удался: %s", e)
            return "Поиск по техкартам временно недоступен."
        if not hits:
            return "В базе техкарт ничего не найдено по этому запросу."
        return "\n\n".join(
            f"[{h.get('title') or 'Техкарта'}]\n{(h.get('content') or '')[:1200]}"
            for h in hits
        )

    return search_tech_cards


def _extract_text(message) -> str:
    if message is None:
        return ""
    parts = []
    for block in getattr(message, "content", []) or []:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()


def run_brewing_agent(
    db,
    report_ctx: Dict[str, Any],
    deviations: List[Dict[str, Any]],
    variety: Optional[str] = None,
) -> Dict[str, Any]:
    """Запустить агента-эксперта на харнессе Tool Runner.

    Возвращает {"model_configured": bool, "text": str|None, "tool_calls": int}.
    """
    if not settings.anthropic_api_key:
        return {"model_configured": False, "text": None, "tool_calls": 0}

    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    search_tech_cards = _build_rag_tool()

    payload = {
        "batch_number": report_ctx.get("batch_number"),
        "variety": variety or report_ctx.get("variety"),
        "container": report_ctx.get("container"),
        "deviations": deviations,
    }
    user_msg = (
        "Разбери отклонения показателей этой партии и дай рекомендации. "
        "Сначала ищи причины в техкартах (search_tech_cards), при необходимости "
        "уточняй внешними источниками (web_search). Данные (JSON):\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )

    tools = [
        search_tech_cards,
        {"type": "web_search_20260209", "name": "web_search", "max_uses": 5},
    ]

    token = _agent_ctx.set({"db": db, "variety": variety or report_ctx.get("variety")})
    tool_calls = 0
    try:
        messages: List[Dict[str, Any]] = [{"role": "user", "content": user_msg}]
        final = None
        restarts = 0
        # Серверный web_search может вернуть pause_turn — Python-раннер не
        # возобновляет его сам; перезапускаем с добавленным приостановленным ходом.
        while True:
            runner = client.beta.messages.tool_runner(
                model=settings.ai_model,
                max_tokens=settings.ai_max_tokens * 4,
                system=_AGENT_SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
            )
            last = None
            for message in runner:
                last = message
                messages.append({"role": "assistant", "content": message.content})
                tool_response = runner.generate_tool_call_response()
                if tool_response is not None:
                    tool_calls += 1
                    messages.append(tool_response)
            if last is None or getattr(last, "stop_reason", None) != "pause_turn":
                final = last
                break
            restarts += 1
            if restarts > 5:
                final = last
                break

        return {
            "model_configured": True,
            "text": _extract_text(final),
            "tool_calls": tool_calls,
        }
    finally:
        _agent_ctx.reset(token)
