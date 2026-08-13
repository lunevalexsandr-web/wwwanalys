"""Подбор нормы из матрицы template_norms по контексту отчёта.

Норма зависит от (показатель, день, сорт, тара, объект). Подбор — «наиболее
специфичное совпадение с фолбэком»: измерение у нормы либо не задано (NULL = любой),
либо должно совпасть с запрошенным; из подходящих берём самую специфичную.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models import TemplateNorm

ZERO_GUID = "00000000-0000-0000-0000-000000000000"


def _guid_eq(a, b) -> bool:
    return a is not None and b is not None and str(a).lower() == str(b).lower()


def resolve_norm(
    db: Session,
    template_id: int,
    indicator_id: int,
    *,
    day: Optional[int] = None,
    variety_key: Optional[str] = None,
    container: Optional[str] = None,
    object_key: Optional[str] = None,
) -> Optional[TemplateNorm]:
    """Вернуть наиболее подходящую норму или None."""
    rows: List[TemplateNorm] = (
        db.query(TemplateNorm)
        .filter(TemplateNorm.template_id == template_id, TemplateNorm.indicator_id == indicator_id)
        .all()
    )
    best: Optional[TemplateNorm] = None
    best_score = -1
    for r in rows:
        score = 0
        ok = True
        # день (числовое сравнение)
        if r.day is not None:
            if day is not None and int(r.day) == int(day):
                score += 1
            else:
                ok = False
        # сорт / объект (GUID)
        for cand, req in ((r.variety_key, variety_key), (r.object_key, object_key)):
            if cand and str(cand) != ZERO_GUID:
                if _guid_eq(cand, req):
                    score += 1
                else:
                    ok = False
        # тара (строка-перечисление)
        if r.container:
            if req_c_match(r.container, container):
                score += 1
            else:
                ok = False
        if not ok:
            continue
        # Строки с реальной нормой (число ИЛИ текст-эталон) имеют приоритет над
        # пустыми: иначе для конкретного дня выбралась бы пустая строка этого дня
        # вместо общей строки с эталоном (напр. «Вкус» → «В норме» без привязки к дню).
        has_norm = (r.min_value is not None or r.max_value is not None
                    or (r.norm_text is not None and str(r.norm_text).strip() != ""))
        if has_norm:
            score += 100
        if score > best_score:
            best_score = score
            best = r
    return best


def req_c_match(cand: str, req: Optional[str]) -> bool:
    return req is not None and str(cand).strip().lower() == str(req).strip().lower()


def variety_key_by_name(db: Session, name: Optional[str]) -> Optional[str]:
    """GUID сорта по его имени (из справочника Variety). None, если не найден."""
    if not name:
        return None
    from app.models import Variety
    v = db.query(Variety).filter(Variety.name == str(name).strip()).first()
    return v.external_id if (v and v.external_id) else None


def get_schedule_days(db: Session, template_id: int, indicator_id: int) -> List[int]:
    """Список дней измерения показателя в шаблоне (по возрастанию). Пусто = одноразовый."""
    rows = (
        db.query(TemplateNorm.day)
        .filter(
            TemplateNorm.template_id == template_id,
            TemplateNorm.indicator_id == indicator_id,
            TemplateNorm.day.isnot(None),
        )
        .distinct()
        .all()
    )
    days = sorted({int(d[0]) for d in rows if d[0] is not None})
    # если есть дни кроме 0 — это расписание (возвращаем все дни); иначе одноразовый
    if any(d != 0 for d in days):
        return days
    return []
