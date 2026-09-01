"""Планировщик санитарных мероприятий: по периодичности из справочника считает
следующий срок каждого мероприятия, сверяет с фактически выполненными и выявляет
просроченные / невыполненные. Событийные («каждый CIP», «каждые N часов работы»)
в календарь не ставятся."""
import re
from datetime import datetime, timedelta

from app.services.daily_digest import msk_now


def freq_to_days(frequency, interval_hours):
    """Периодичность → интервал в днях. None — событийное/неопределённое (не планируем)."""
    if interval_hours and interval_hours > 0:
        return interval_hours / 24.0
    f = (frequency or "").strip().lower()
    if not f:
        return None
    # событийные — привязаны к CIP/наработке, не к календарю
    if "cip" in f or "часов работы" in f or "по событию" in f or ("по графику" in f and not re.search(r"\d", f)):
        return None
    m = re.search(r"кажд\w*\s+(\d+)\s*час", f)          # «каждые 12 часов»
    if m:
        return int(m.group(1)) / 24.0
    if "год" in f:
        return 365.0
    if "квартал" in f or "три месяца" in f or "3 месяца" in f:
        return 90.0
    if "2 недел" in f or "две недел" in f:
        return 14.0
    if "месяц" in f or "мес" in f:
        return 30.0
    if "недел" in f:
        return 7.0
    m = re.search(r"(\d+)\s*дн", f)                     # «7 дней», «в 7 дней»
    if m:
        return float(m.group(1))
    if "сутк" in f:
        return 1.0
    return None


def compute_sanitation_compliance(db, as_of=None):
    """Вернуть {as_of, overdue, planned, event_based} по санитарным мероприятиям.

    overdue — просроченные/невыполненные (срок прошёл или ни разу не выполнялось);
    planned — в норме, с датой следующего срока;
    event_based — событийные (без календарного планирования).
    """
    from sqlalchemy import func
    from app.models import SanitationMeasure, SanitationRecord

    if as_of is None:
        as_of = msk_now().date()
    if isinstance(as_of, datetime):
        as_of = as_of.date()

    # последнее фактическое выполнение и подразделение по названию мероприятия
    last_map = dict(
        db.query(SanitationRecord.measure_name, func.max(SanitationRecord.period))
        .group_by(SanitationRecord.measure_name).all()
    )
    dept_rows = (db.query(SanitationRecord.measure_name, SanitationRecord.department_name)
                 .filter(SanitationRecord.department_name.isnot(None)).all())
    dept_map = {}
    for name, dept in dept_rows:
        if name and dept and name not in dept_map:
            dept_map[name] = dept

    overdue, planned, event_based = [], [], []
    for m in db.query(SanitationMeasure).all():
        days = freq_to_days(m.frequency, m.interval_hours)
        if days is None:
            event_based.append({"мероприятие": m.name, "частота": m.frequency or "по событию",
                                 "подразделение": dept_map.get(m.name)})
            continue
        last = last_map.get(m.name)
        last_d = last.date() if last else None
        item = {
            "мероприятие": m.name,
            "частота": m.frequency,
            "интервал_дн": round(days, 1),
            "подразделение": dept_map.get(m.name),
            "последнее": last_d.isoformat() if last_d else None,
        }
        if last_d is None:
            item.update({"след_срок": None, "просрочка_дн": None, "статус": "ни разу не выполнялось"})
            overdue.append(item)
            continue
        next_due = last_d + timedelta(days=int(round(days)))
        overdue_days = (as_of - next_due).days
        item["след_срок"] = next_due.isoformat()
        item["просрочка_дн"] = overdue_days
        if overdue_days > 0:
            item["статус"] = "просрочено"
            overdue.append(item)
        else:
            item["статус"] = "в норме"
            planned.append(item)

    overdue.sort(key=lambda x: x["просрочка_дн"] if x["просрочка_дн"] is not None else 10 ** 6, reverse=True)
    planned.sort(key=lambda x: x["след_срок"] or "9999")
    return {"as_of": as_of.isoformat(), "overdue": overdue, "planned": planned, "event_based": event_based}


def plan_for_day(db, as_of=None, horizon_days=0):
    """План санитарных мероприятий на день: просроченные (сделать в первую очередь) +
    плановые, срок которых наступает сегодня (или в пределах horizon_days).

    Возвращает {as_of, план:[{мероприятие, частота, подразделение, последнее, срок,
    причина, приоритет, длительность_мин?}]}.
    """
    from datetime import date as _date, timedelta as _td
    res = compute_sanitation_compliance(db, as_of)
    as_of_d = _date.fromisoformat(res["as_of"])
    plan = []
    for o in res["overdue"]:
        if o.get("статус") == "ни разу не выполнялось":
            reason, prio, order = "ни разу не выполнялось", "просрочено", -10 ** 6
        else:
            reason, prio, order = f"просрочено {o['просрочка_дн']} дн", "просрочено", -(o.get("просрочка_дн") or 0)
        plan.append({
            "мероприятие": o["мероприятие"], "частота": o.get("частота"),
            "подразделение": o.get("подразделение"), "последнее": o.get("последнее"),
            "срок": o.get("след_срок"), "причина": reason, "приоритет": prio, "_o": order,
        })
    for p in res["planned"]:
        due = p.get("след_срок")
        if not due:
            continue
        try:
            dd = _date.fromisoformat(due)
        except Exception:
            continue
        delta = (dd - as_of_d).days
        if delta <= horizon_days:
            plan.append({
                "мероприятие": p["мероприятие"], "частота": p.get("частота"),
                "подразделение": p.get("подразделение"), "последнее": p.get("последнее"),
                "срок": due, "причина": ("по графику сегодня" if delta == 0 else f"по графику ({due})"),
                "приоритет": "сегодня", "_o": 10 + delta,
            })
    plan.sort(key=lambda x: x.pop("_o"))
    return {"as_of": res["as_of"], "всего": len(plan), "план": plan}
