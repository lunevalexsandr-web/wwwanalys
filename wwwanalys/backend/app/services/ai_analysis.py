"""
AI-ассистент «эксперт-пивовар»: разбор отклонений показателей в отчёте.

Архитектура — два независимых слоя:

1. Движок отклонений (compute_deviations) — чистый Python, БЕЗ модели.
   Сравнивает значения показателей с нормами шаблона, считает направление и % —
   работает всегда и является источником всех чисел.

2. Экспертный слой (провайдеры) — трактовка/причины/рекомендации текстом.
   Спрятан за интерфейсом ExpertProvider, поэтому конкретную модель
   (Anthropic / локальная Ollama / GigaChat / YandexGPT / …) можно выбрать позже,
   не меняя движок, API и интерфейс. Пока модель не выбрана, работает провайдер
   "none": возвращаются только факты по отклонениям, без текстового разбора.

Модель НИКОГДА не выдумывает числа — факты считаются в коде и передаются как есть.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import IndicatorLibrary, TemplateIndicator, ProcessLog, AnalysisType

logger = logging.getLogger(__name__)


# ==================== Сбор контекста отчёта ====================

def build_report_context(db: Session, report: ProcessLog) -> Dict[str, Any]:
    """Собрать значения показателей отчёта с нормами (min/max) из шаблона."""
    from app.services.norms import resolve_norm, variety_key_by_name
    template = db.query(AnalysisType).filter(AnalysisType.id == report.analysis_type_id).first()
    vkey = variety_key_by_name(db, getattr(report, "variety", None))
    values: List[Dict[str, Any]] = []
    for v in (report.indicator_values or []):
        lib = db.query(IndicatorLibrary).filter(IndicatorLibrary.id == v.indicator_id).first()
        # норма: из матрицы (день+сорт+тара), фолбэк на TemplateIndicator
        mn = mx = None
        norm = resolve_norm(
            db, report.analysis_type_id, v.indicator_id,
            day=getattr(v, "day", None), container=getattr(report, "container", None),
            variety_key=vkey, object_key=getattr(report, "object_key", None),
        )
        if norm is not None:
            mn, mx = norm.min_value, norm.max_value
        if mn is None and mx is None:
            ti = db.query(TemplateIndicator).filter(
                TemplateIndicator.indicator_id == v.indicator_id,
                TemplateIndicator.template_id == report.analysis_type_id,
            ).first()
            if ti:
                mn, mx = ti.min_value, ti.max_value
        values.append({
            "indicator_id": v.indicator_id,
            "name": lib.name if lib else f"Показатель #{v.indicator_id}",
            "unit": (lib.unit if lib else "") or "",
            "value": v.value,
            "text_value": v.text_value,
            "day": getattr(v, "day", None),
            "min_value": mn,
            "max_value": mx,
        })
    return {
        "batch_number": report.batch_number,
        "variety": getattr(report, "variety", None),
        "template_name": template.name if template else None,
        "values": values,
    }


# ==================== Слой 1: расчёт отклонений (без модели) ====================

def compute_deviations(values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Найти показатели, вышедшие за норму (числовые). Возвращает список отклонений."""
    deviations: List[Dict[str, Any]] = []
    for v in values:
        val = v.get("value")
        mn = v.get("min_value")
        mx = v.get("max_value")
        if val is None:
            continue  # текстовые показатели или без значения — пропускаем
        if mn is None and mx is None:
            continue  # нет нормы — сравнивать не с чем
        below = mn is not None and val < mn
        above = mx is not None and val > mx
        if not (below or above):
            continue

        # Насколько вышли за границу (в процентах от превышенной границы)
        dev_pct: Optional[float] = None
        if below and mn not in (None, 0):
            dev_pct = round((mn - val) / abs(mn) * 100, 1)
        elif above and mx not in (None, 0):
            dev_pct = round((val - mx) / abs(mx) * 100, 1)

        norm = _format_norm(mn, mx)
        deviations.append({
            "indicator": v["name"],
            "unit": v.get("unit", ""),
            "value": val,
            "min_value": mn,
            "max_value": mx,
            "norm": norm,
            "direction": "below" if below else "above",
            "deviation_pct": dev_pct,
        })
    return deviations


def _format_norm(mn: Optional[float], mx: Optional[float]) -> str:
    if mn is not None and mx is not None:
        return f"{_num(mn)}–{_num(mx)}"
    if mn is not None:
        return f"≥ {_num(mn)}"
    if mx is not None:
        return f"≤ {_num(mx)}"
    return ""


def _num(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else str(x)


# ==================== Слой 2: экспертные провайдеры ====================

_SYSTEM_PROMPT = (
    "Ты — опытный технолог-пивовар и заведующий производственной лабораторией "
    "пивоваренного завода. Тебе дают показатели анализа партии пива, вышедшие "
    "за установленные нормы. По каждому отклонению дай краткий экспертный разбор: "
    "что это значит для качества/стойкости/вкуса партии, наиболее вероятные "
    "технологические причины (варка, затирание, брожение, дображивание, розлив, "
    "вода, дрожжи, оборудование) и конкретные практические действия для исправления "
    "и предотвращения. Опирайся только на переданные факты и нормы, не выдумывай "
    "числовые значения. Отвечай на русском языке, по делу, без общих фраз. "
    "Ты — советник: окончательное решение принимает технолог."
)


def _build_user_payload(report_ctx: Dict[str, Any], deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Единый набор фактов для любой модели."""
    return {
        "batch_number": report_ctx.get("batch_number"),
        "template": report_ctx.get("template_name"),
        "deviations": [
            {
                "indicator": d["indicator"],
                "unit": d["unit"],
                "value": d["value"],
                "norm": d["norm"],
                "direction": "ниже нормы" if d["direction"] == "below" else "выше нормы",
                "deviation_pct": d["deviation_pct"],
            }
            for d in deviations
        ],
    }


def _format_knowledge(knowledge: Optional[List[Dict[str, Any]]]) -> str:
    """Собрать выдержки из техкарты в текстовый блок для промпта."""
    if not knowledge:
        return ""
    parts = []
    for k in knowledge:
        src = k.get("title") or "техкарта"
        parts.append(f"[{src}] {k.get('content', '').strip()}")
    return "\n---\n".join(parts)


class ExpertProvider:
    """Интерфейс экспертного слоя. Реализация переводит факты в текстовый разбор."""

    name: str = "base"

    def is_configured(self) -> bool:
        raise NotImplementedError

    def analyze(
        self,
        report_ctx: Dict[str, Any],
        deviations: List[Dict[str, Any]],
        knowledge: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Вернуть {summary: str, deviations: [{indicator, severity, interpretation,
        likely_causes[], actions[]}]}.

        knowledge — релевантные фрагменты техкарты сорта из базы знаний (RAG),
        используются как заземление; провайдер может их игнорировать.
        """
        raise NotImplementedError


class NoneProvider(ExpertProvider):
    """Заглушка: модель не выбрана. Возвращает факты без текстового разбора."""

    name = "none"

    def is_configured(self) -> bool:
        return True  # всегда доступна — деградация к «только факты»

    def analyze(self, report_ctx, deviations, knowledge=None) -> Dict[str, Any]:
        return {
            "summary": (
                f"Найдено отклонений: {len(deviations)}. "
                "Текстовый разбор эксперта появится после подключения модели "
                "(настройка AI_PROVIDER на сервере)."
            ),
            "model_configured": False,
            "deviations": [
                {
                    "indicator": d["indicator"],
                    "severity": _fallback_severity(d),
                    "interpretation": "",
                    "likely_causes": [],
                    "actions": [],
                }
                for d in deviations
            ],
        }


def _fallback_severity(d: Dict[str, Any]) -> str:
    """Грубая оценка критичности по величине отклонения (когда модели нет)."""
    pct = d.get("deviation_pct")
    if pct is None:
        return "medium"
    if pct >= 25:
        return "high"
    if pct >= 10:
        return "medium"
    return "low"


_ANTHROPIC_TOOL = {
    "name": "report_deviation_analysis",
    "description": "Вернуть экспертный разбор отклонений показателей партии пива.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "Краткий общий вывод по партии, 1–2 предложения."},
            "deviations": {
                "type": "array",
                "description": "По одному элементу на каждое переданное отклонение.",
                "items": {
                    "type": "object",
                    "properties": {
                        "indicator": {"type": "string", "description": "Название показателя (как в исходных данных)."},
                        "severity": {"type": "string", "enum": ["low", "medium", "high"],
                                     "description": "Критичность отклонения для партии."},
                        "interpretation": {"type": "string", "description": "Что это отклонение означает для партии."},
                        "likely_causes": {"type": "array", "items": {"type": "string"},
                                          "description": "Вероятные технологические причины (2–4 пункта)."},
                        "actions": {"type": "array", "items": {"type": "string"},
                                    "description": "Конкретные шаги для исправления/предотвращения (2–4 пункта)."},
                    },
                    "required": ["indicator", "severity", "interpretation", "likely_causes", "actions"],
                },
            },
        },
        "required": ["summary", "deviations"],
    },
}


class AnthropicProvider(ExpertProvider):
    """Экспертный разбор через Claude (structured output, forced tool-use)."""

    name = "anthropic"

    def is_configured(self) -> bool:
        return bool(settings.anthropic_api_key)

    def analyze(self, report_ctx, deviations, knowledge=None) -> Dict[str, Any]:
        from anthropic import Anthropic

        client = Anthropic(api_key=settings.anthropic_api_key)
        payload = _build_user_payload(report_ctx, deviations)
        user_msg = "Разбери отклонения показателей этой партии. Данные (JSON):\n" + \
            json.dumps(payload, ensure_ascii=False, indent=2)
        kb = _format_knowledge(knowledge)
        if kb:
            user_msg += (
                "\n\nВыдержки из технологической карты сорта (опирайся на них "
                "как на приоритетный источник; если они противоречат общим "
                "представлениям — верь карте):\n" + kb
            )
        resp = client.messages.create(
            model=settings.ai_model,
            max_tokens=settings.ai_max_tokens,
            system=_SYSTEM_PROMPT,
            tools=[_ANTHROPIC_TOOL],
            tool_choice={"type": "tool", "name": "report_deviation_analysis"},
            messages=[{"role": "user", "content": user_msg}],
        )
        for block in resp.content:
            if block.type == "tool_use" and block.name == "report_deviation_analysis":
                out = dict(block.input)
                out["model_configured"] = True
                return out
        raise RuntimeError("Модель не вернула структурированный разбор")


# Реестр провайдеров. Новую модель добавить = зарегистрировать класс здесь.
_PROVIDERS = {
    "none": NoneProvider,
    "anthropic": AnthropicProvider,
}


def get_provider() -> ExpertProvider:
    """Выбрать экспертный провайдер по настройкам.

    "auto" — взять первый настроенный из известных; иначе NoneProvider.
    Явное имя — взять именно его (или NoneProvider, если не настроен).
    """
    choice = (settings.ai_provider or "auto").strip().lower()

    if choice == "auto":
        for cls in (AnthropicProvider,):  # порядок = приоритет автовыбора
            p = cls()
            if p.is_configured():
                return p
        return NoneProvider()

    cls = _PROVIDERS.get(choice)
    if cls is None:
        logger.warning("Неизвестный AI_PROVIDER=%r, использую 'none'", choice)
        return NoneProvider()
    provider = cls()
    if not provider.is_configured():
        logger.warning("AI_PROVIDER=%r не настроен, использую 'none'", choice)
        return NoneProvider()
    return provider
