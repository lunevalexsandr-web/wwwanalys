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


def _rag_search(db, query: str, variety: Optional[str]) -> str:
    """Общий поиск по базе техкарт (RAG). Используется обоими движками агента."""
    if db is None or not query:
        return "База техкарт недоступна."
    try:
        from app.services.rag import search_chunks
        hits = search_chunks(db, query, variety=variety, limit=5)
    except Exception as e:
        logger.warning("RAG-поиск в агенте не удался: %s", e)
        return "Поиск по техкартам временно недоступен."
    if not hits:
        return "В базе техкарт ничего не найдено по этому запросу."
    return "\n\n".join(
        f"[{h.get('title') or 'Техкарта'}]\n{(h.get('content') or '')[:1200]}"
        for h in hits
    )


def _build_user_msg(report_ctx: Dict[str, Any], deviations: List[Dict[str, Any]],
                    variety: Optional[str]) -> str:
    payload = {
        "batch_number": report_ctx.get("batch_number"),
        "variety": variety or report_ctx.get("variety"),
        "container": report_ctx.get("container"),
        "deviations": deviations,
    }
    return (
        "Разбери отклонения показателей этой партии и дай рекомендации. "
        "Сначала ищи причины в техкартах (search_tech_cards), при необходимости "
        "опирайся на внешние источники. Данные (JSON):\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


_PERIOD_AGENT_SYSTEM_PROMPT = (
    "Ты — эксперт-пивовар и технолог лаборатории. Разбираешь СВОДКУ отклонений "
    "показателей за период по всем отчётам и даёшь рекомендации по улучшению.\n\n"
    "Инструменты: search_tech_cards — ищи причины и регламенты во внутренней базе "
    "техкарт (приоритет); при необходимости опирайся на внешние источники.\n\n"
    "Числа в сводке даны как факты — не изменяй их. Дай: общую картину качества за "
    "период, топ проблемных показателей и вероятные системные причины, конкретные "
    "корректирующие действия, и краткое резюме. Отвечай на русском, структурно."
)


def _build_period_user_msg(analytics: Dict[str, Any]) -> str:
    """Сжать аналитику периода в компактный JSON для модели."""
    payload = {
        "период": {"с": analytics.get("date_from"), "по": analytics.get("date_to")},
        "отчётов": analytics.get("reports_count"),
        "отчётов_с_отклонением": analytics.get("reports_with_deviations"),
        "показателей_всего": analytics.get("values_count"),
        "отклонений": analytics.get("deviations_count"),
        "доля_отклонений_%": analytics.get("deviation_rate"),
        "по_дням": analytics.get("by_day"),
        "топ_показателей_по_отклонениям": analytics.get("top_indicators"),
        "по_шаблонам": analytics.get("by_template"),
        # список отклонений может быть большим — берём до 80 записей
        "примеры_отклонений": (analytics.get("deviations") or [])[:80],
    }
    return (
        "Разбери сводку отклонений за период и дай рекомендации. Сначала ищи "
        "причины в техкартах (search_tech_cards). Данные (JSON):\n"
        + json.dumps(payload, ensure_ascii=False, indent=2, default=str)
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
    """Запустить агента-эксперта. Провайдер выбирается по наличию ключа:
    OpenRouter (OpenAI-совместимый) → иначе Anthropic Tool Runner.

    Возвращает {"model_configured": bool, "text": str|None, "tool_calls": int}.
    """
    variety = variety or report_ctx.get("variety")
    user_msg = _build_user_msg(report_ctx, deviations, variety)
    return _dispatch(db, _AGENT_SYSTEM_PROMPT, user_msg, variety)


def run_period_agent(db, analytics: Dict[str, Any]) -> Dict[str, Any]:
    """Агентный разбор всех отклонений за период (для страницы «Аналитика»)."""
    user_msg = _build_period_user_msg(analytics)
    return _dispatch(db, _PERIOD_AGENT_SYSTEM_PROMPT, user_msg, variety=None)


def _dispatch(db, system_prompt: str, user_msg: str, variety: Optional[str]) -> Dict[str, Any]:
    """Выбрать провайдера по наличию ключа: OpenRouter → иначе Anthropic Tool Runner."""
    if settings.openrouter_api_key:
        return _run_openrouter(db, system_prompt, user_msg, variety)
    if settings.anthropic_api_key:
        return _run_anthropic(db, system_prompt, user_msg, variety)
    return {"model_configured": False, "text": None, "tool_calls": 0}


def _run_openrouter(db, system_prompt: str, user_msg: str, variety) -> Dict[str, Any]:
    """Агент через OpenRouter (OpenAI SDK): function-calling для RAG + веб-плагин."""
    from openai import OpenAI

    client = OpenAI(base_url=settings.openrouter_base_url, api_key=settings.openrouter_api_key)
    tools = [{
        "type": "function",
        "function": {
            "name": "search_tech_cards",
            "description": "Поиск во внутренней базе технологических карт (RAG). "
                           "Возвращает выдержки из регламентов предприятия.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "запрос на русском"}},
                "required": ["query"],
            },
        },
    }]
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]
    tool_calls = 0
    last_text = ""
    for _ in range(6):
        resp = client.chat.completions.create(
            model=settings.openrouter_model,
            messages=messages,
            tools=tools,
            max_tokens=settings.ai_max_tokens * 4,
            extra_body={"plugins": [{"id": "web", "max_results": 5}]},  # внешние источники
        )
        msg = resp.choices[0].message
        last_text = (msg.content or "").strip()
        if getattr(msg, "tool_calls", None):
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [{
                    "id": tc.id, "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                } for tc in msg.tool_calls],
            })
            for tc in msg.tool_calls:
                tool_calls += 1
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = _rag_search(db, args.get("query", ""), variety)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            continue
        break
    return {"model_configured": True, "text": last_text, "tool_calls": tool_calls}


def _run_anthropic(db, system_prompt: str, user_msg: str, variety) -> Dict[str, Any]:
    """Запустить агента-эксперта на харнессе Anthropic Tool Runner (RAG + web_search)."""
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    search_tech_cards = _build_rag_tool()

    tools = [
        search_tech_cards,
        {"type": "web_search_20260209", "name": "web_search", "max_uses": 5},
    ]

    token = _agent_ctx.set({"db": db, "variety": variety})
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
                system=system_prompt,
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


# ==================== Чат с агентом (вопрос-ответ по данным) ====================

_CHAT_SYSTEM_PROMPT = (
    "Ты — ассистент лаборатории и эксперт-пивовар. Отвечаешь на вопросы технолога "
    "по данным анализов и помогаешь с отклонениями.\n"
    "Сегодняшняя дата: {today}. «вчера», «сегодня», «за неделю» считай от неё.\n\n"
    "Инструменты: get_deviations_by_date (за день), get_period_summary (за период), "
    "get_report_deviations (по номеру партии), search_tech_cards (внутренние техкарты, "
    "приоритетный источник), плюс внешние источники при необходимости.\n\n"
    "ВАЖНО: все вопросы — про лабораторные анализы и производство пива этого предприятия, "
    "а НЕ про новости или мировые события. «Что произошло за день/период» = какие анализы "
    "и отклонения были — вызывай get_deviations_by_date/get_period_summary. Никогда не "
    "отвечай новостями.\n"
    "Правила: числа по отклонениям бери только из инструментов, не выдумывай. На вопрос "
    "«что произошло за день/период» — вызови инструмент и перечисли отклонения (партия, "
    "показатель, значение, норма) + краткий вывод. На просьбу помочь с отклонением — "
    "предложи вероятные причины и корректирующие действия по техкартам. Отвечай на русском.\n\n"
    "ФОРМАТ ОТВЕТА: по умолчанию давай ТОЛЬКО блок «📌 Кратко:» — 2–4 пункта с главным "
    "(сколько отклонений, самое важное, что делать). Раздел «Подробно:» добавляй ТОЛЬКО "
    "если пользователь явно просит подробности (слова «подробно», «детально», «расскажи "
    "полностью», «раскрой» и т.п.). Без такой просьбы подробности не выводи, можешь в конце "
    "добавить строку «Нужны подробности — спросите.»."
)


def _tool_deviations_by_date(db, args) -> str:
    from datetime import date
    from app.services import ai_analysis
    d = (args or {}).get("date")
    try:
        dd = date.fromisoformat(str(d))
    except Exception:
        return "Нужна дата в формате YYYY-MM-DD."
    a = ai_analysis.build_period_analytics(db, date_from=dd, date_to=dd)
    return json.dumps({
        "дата": str(dd),
        "отчётов": a.get("reports_count"),
        "отчётов_с_отклонением": a.get("reports_with_deviations"),
        "отклонений": a.get("deviations_count"),
        "отклонения": (a.get("deviations") or [])[:100],
    }, ensure_ascii=False, default=str)


def _tool_period_summary(db, args) -> str:
    from datetime import date
    from app.services import ai_analysis
    a = args or {}
    try:
        df = date.fromisoformat(str(a.get("date_from")))
        dt = date.fromisoformat(str(a.get("date_to")))
    except Exception:
        return "Нужны date_from и date_to (YYYY-MM-DD)."
    an = ai_analysis.build_period_analytics(db, date_from=df, date_to=dt)
    return json.dumps({
        "период": {"с": str(df), "по": str(dt)},
        "отчётов": an.get("reports_count"),
        "отчётов_с_отклонением": an.get("reports_with_deviations"),
        "отклонений": an.get("deviations_count"),
        "доля_%": an.get("deviation_rate"),
        "топ_показателей": an.get("top_indicators"),
        "по_шаблонам": an.get("by_template"),
        "примеры_отклонений": (an.get("deviations") or [])[:60],
    }, ensure_ascii=False, default=str)


def _tool_report_deviations(db, args) -> str:
    from app.models import ProcessLog
    from app.crud import report as crud_report
    from app.services import ai_analysis
    batch = (args or {}).get("batch_number")
    if not batch:
        return "Нужен batch_number (номер партии)."
    logs = db.query(ProcessLog).filter(ProcessLog.batch_number == str(batch)).all()
    if not logs:
        return "Отчётов с такой партией не найдено."
    out = []
    for pl in logs:
        rep = crud_report.get_report(db, report_id=pl.id)
        ctx = ai_analysis.build_report_context(db, rep)
        devs = ai_analysis.compute_deviations(ctx["values"])
        out.append({
            "report_id": pl.id,
            "template": ctx.get("template_name"),
            "variety": ctx.get("variety"),
            "container": ctx.get("container"),
            "deviations": devs,
        })
    return json.dumps(out, ensure_ascii=False, default=str)


_CHAT_TOOL_DEFS = [
    {"name": "get_deviations_by_date",
     "description": "Отклонения показателей за конкретный день по всем отчётам.",
     "params": {"type": "object", "properties": {"date": {"type": "string", "description": "дата YYYY-MM-DD"}}, "required": ["date"]}},
    {"name": "get_period_summary",
     "description": "Сводка отклонений за период (агрегаты + топ показателей/шаблонов).",
     "params": {"type": "object", "properties": {"date_from": {"type": "string"}, "date_to": {"type": "string"}}, "required": ["date_from", "date_to"]}},
    {"name": "get_report_deviations",
     "description": "Отклонения по конкретной партии (номер партии).",
     "params": {"type": "object", "properties": {"batch_number": {"type": "string"}}, "required": ["batch_number"]}},
    {"name": "search_tech_cards",
     "description": "Поиск во внутренней базе технологических карт (RAG).",
     "params": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
]

_CHAT_EXEC = {
    "get_deviations_by_date": _tool_deviations_by_date,
    "get_period_summary": _tool_period_summary,
    "get_report_deviations": _tool_report_deviations,
    "search_tech_cards": lambda db, a: _rag_search(db, (a or {}).get("query", ""), None),
}


def _exec_chat_tool(db, name, args) -> str:
    fn = _CHAT_EXEC.get(name)
    if not fn:
        return "Неизвестный инструмент: " + str(name)
    try:
        return fn(db, args)
    except Exception as e:
        logger.warning("Инструмент %s упал: %s", name, e)
        return "Ошибка инструмента " + str(name) + ": " + str(e)


def run_chat_agent(db, history: List[Dict[str, str]]) -> Dict[str, Any]:
    """Чат с агентом. history — список {role: user|assistant, content}."""
    import datetime
    today = datetime.date.today().isoformat()
    system_prompt = _CHAT_SYSTEM_PROMPT.format(today=today)
    if settings.openrouter_api_key:
        return _chat_openrouter(db, system_prompt, history)
    if settings.anthropic_api_key:
        return _chat_anthropic(db, system_prompt, history)
    return {"model_configured": False, "text": None}


def _chat_openrouter(db, system_prompt, history) -> Dict[str, Any]:
    from openai import OpenAI
    client = OpenAI(base_url=settings.openrouter_base_url, api_key=settings.openrouter_api_key)
    tools = [{"type": "function", "function": {"name": d["name"], "description": d["description"], "parameters": d["params"]}}
             for d in _CHAT_TOOL_DEFS]
    messages = [{"role": "system", "content": system_prompt}]
    for m in history:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            messages.append({"role": m["role"], "content": m["content"]})
    last_text = ""
    for _ in range(8):
        # Без авто-веб-плагина: чат отвечает по данным анализов и техкартам,
        # чтобы вопрос «что произошло за день» не подменялся новостями из веба.
        resp = client.chat.completions.create(
            model=settings.openrouter_model, messages=messages, tools=tools,
            max_tokens=settings.ai_max_tokens * 4,
        )
        msg = resp.choices[0].message
        last_text = (msg.content or "").strip()
        if getattr(msg, "tool_calls", None):
            messages.append({
                "role": "assistant", "content": msg.content or "",
                "tool_calls": [{"id": tc.id, "type": "function",
                                "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                               for tc in msg.tool_calls],
            })
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                messages.append({"role": "tool", "tool_call_id": tc.id,
                                 "content": _exec_chat_tool(db, tc.function.name, args)})
            continue
        break
    return {"model_configured": True, "text": last_text}


def _chat_anthropic(db, system_prompt, history) -> Dict[str, Any]:
    from anthropic import Anthropic
    client = Anthropic(api_key=settings.anthropic_api_key)
    tools = [{"name": d["name"], "description": d["description"], "input_schema": d["params"]}
             for d in _CHAT_TOOL_DEFS]
    tools.append({"type": "web_search_20260209", "name": "web_search", "max_uses": 5})
    messages = [{"role": m["role"], "content": m["content"]}
                for m in history if m.get("role") in ("user", "assistant") and m.get("content")]
    resp = None
    for _ in range(8):
        resp = client.messages.create(
            model=settings.ai_model, max_tokens=settings.ai_max_tokens * 4,
            system=system_prompt, tools=tools, messages=messages,
        )
        if resp.stop_reason in ("tool_use", "pause_turn"):
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for block in resp.content:
                if getattr(block, "type", None) == "tool_use" and block.name in _CHAT_EXEC:
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": _exec_chat_tool(db, block.name, dict(block.input))})
            if results:
                messages.append({"role": "user", "content": results})
            continue
        break
    return {"model_configured": True, "text": _extract_text(resp) if resp else ""}
