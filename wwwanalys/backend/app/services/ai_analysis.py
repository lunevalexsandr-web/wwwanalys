"""
AI-ассистент «эксперт-пивовар»: разбор отклонений показателей в отчёте.

Два слоя:
1. compute_deviations() — детерминированный расчёт отклонений от норм (без ИИ).
2. analyze_deviations() — экспертная трактовка/причины/рекомендации через Claude
   (модель эксперта-пивовара), строго структурированный ответ через tool-use.

Данные (факты, нормы) считаются в коде и передаются модели как есть — модель
не выдумывает числа, а только трактует и советует.
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
    template = db.query(AnalysisType).filter(AnalysisType.id == report.analysis_type_id).first()
    values: List[Dict[str, Any]] = []
    for v in (report.indicator_values or []):
        lib = db.query(IndicatorLibrary).filter(IndicatorLibrary.id == v.indicator_id).first()
        ti = db.query(TemplateIndicator).filter(
            TemplateIndicator.indicator_id == v.indicator_id,
            TemplateIndicator.template_id == report.analysis_type_id,
        ).first()
        values.append({
            "indicator_id": v.indicator_id,
            "name": lib.name if lib else f"Показатель #{v.indicator_id}",
            "unit": (lib.unit if lib else "") or "",
            "value": v.value,
            "text_value": v.text_value,
            "min_value": ti.min_value if ti else None,
            "max_value": ti.max_value if ti else None,
        })
    return {
        "batch_number": report.batch_number,
        "template_name": template.name if template else None,
        "values": values,
    }


# ==================== Слой 1: расчёт отклонений ====================

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


# ==================== Слой 2: экспертный разбор через Claude ====================

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

_ANALYSIS_TOOL = {
    "name": "report_deviation_analysis",
    "description": "Вернуть экспертный разбор отклонений показателей партии пива.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Краткий общий вывод по партии, 1–2 предложения.",
            },
            "deviations": {
                "type": "array",
                "description": "По одному элементу на каждое переданное отклонение.",
                "items": {
                    "type": "object",
                    "properties": {
                        "indicator": {"type": "string", "description": "Название показателя (как в исходных данных)."},
                        "severity": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Критичность отклонения для партии.",
                        },
                        "interpretation": {"type": "string", "description": "Что это отклонение означает для партии."},
                        "likely_causes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Вероятные технологические причины (2–4 пункта).",
                        },
                        "actions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Конкретные шаги для исправления/предотвращения (2–4 пункта).",
                        },
                    },
                    "required": ["indicator", "severity", "interpretation", "likely_causes", "actions"],
                },
            },
        },
        "required": ["summary", "deviations"],
    },
}


def is_ai_configured() -> bool:
    return bool(settings.anthropic_api_key)


def analyze_deviations(report_ctx: Dict[str, Any], deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Экспертный разбор отклонений через Claude. Возвращает {summary, deviations:[...]}."""
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    payload = {
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
    user_msg = (
        "Разбери отклонения показателей этой партии. "
        "Данные (JSON):\n" + json.dumps(payload, ensure_ascii=False, indent=2)
    )
    resp = client.messages.create(
        model=settings.ai_model,
        max_tokens=settings.ai_max_tokens,
        system=_SYSTEM_PROMPT,
        tools=[_ANALYSIS_TOOL],
        tool_choice={"type": "tool", "name": "report_deviation_analysis"},
        messages=[{"role": "user", "content": user_msg}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "report_deviation_analysis":
            return block.input
    raise RuntimeError("Модель не вернула структурированный разбор")
