"""Ежедневная сводка «дежурного агента»: импорт за день из 1С → отклонения →
разбор агента (что исправить) → допущенные/недопущенные партии → сохранение сводки."""
import json
import logging
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)

# Московское время (UTC+3, без перехода на летнее время)
MSK_OFFSET = timedelta(hours=3)


def msk_now():
    return datetime.utcnow() + MSK_OFFSET


def agents_enabled(db) -> bool:
    """Главный рубильник всех агентов (по умолчанию включены)."""
    try:
        s = get_or_create_schedule(db)
        return bool(getattr(s, "agents_enabled", True))
    except Exception:
        return True


def get_or_create_schedule(db):
    from app.models import DigestSchedule
    s = db.query(DigestSchedule).first()
    if not s:
        s = DigestSchedule(enabled=False, run_time="07:00", day_mode="yesterday")
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def compute_released(db, target_date):
    """Допущенные / недопущенные партии за день по показателю «Допуск к розливу» = «Допуск»."""
    from sqlalchemy import func
    from app.models import ProcessLog, IndicatorValue, IndicatorLibrary
    rows = (db.query(ProcessLog.id, ProcessLog.batch_number, ProcessLog.variety,
                     ProcessLog.container, IndicatorValue.text_value)
            .join(IndicatorValue, IndicatorValue.process_log_id == ProcessLog.id)
            .join(IndicatorLibrary, IndicatorLibrary.id == IndicatorValue.indicator_id)
            .filter(func.date(ProcessLog.started_at) == target_date,
                    IndicatorLibrary.name.ilike("%допуск%"))
            .all())
    released, not_released = {}, {}
    for rid, batch, variety, container, val in rows:
        v = (val or "").strip().lower()
        key = batch if (batch or "").strip() else f"#{rid}"
        item = {"batch": batch or f"#{rid}", "variety": variety, "container": container, "value": val, "report_id": rid}
        if v == "допуск":
            released[key] = item
            not_released.pop(key, None)
        elif key not in released:
            not_released[key] = item

    # Причина недопуска: по каким показателям отклонения (все, если их несколько)
    from app.crud import report as crud_report
    from app.services import ai_analysis
    for item in not_released.values():
        reasons = []
        try:
            rep = crud_report.get_report(db, report_id=item["report_id"])
            if rep:
                ctx = ai_analysis.build_report_context(db, rep)
                for d in ai_analysis.compute_deviations(ctx["values"]):
                    reasons.append({
                        "indicator": d["indicator"],
                        "value": d.get("value"),
                        "unit": d.get("unit", ""),
                        "norm": d.get("norm"),
                    })
        except Exception:
            pass
        item["reasons"] = reasons
    return list(released.values()), list(not_released.values())


def compute_deviation_rows(db, target_date):
    """Все отклонения показателей за день по отчётам: партия, сорт, ёмкость (танк из
    показателей), показатель, значение, норма, направление."""
    from sqlalchemy import func
    from app.models import ProcessLog
    from app.crud import report as crud_report
    from app.services import ai_analysis

    logs = db.query(ProcessLog).filter(func.date(ProcessLog.started_at) == target_date).all()
    rows = []
    for pl in logs:
        rep = crud_report.get_report(db, report_id=pl.id)
        if not rep:
            continue
        ctx = ai_analysis.build_report_context(db, rep)
        devs = ai_analysis.compute_deviations(ctx["values"])
        if not devs:
            continue
        # ёмкость: показатель с «танк/ёмк/емк/цкт» в названии
        tank = None
        for val in ctx["values"]:
            nm = (val.get("name") or "").lower()
            if any(k in nm for k in ("танк", "ёмк", "емк", "цкт", "бак")):
                tank = val.get("value") if val.get("value") is not None else val.get("text_value")
                if tank not in (None, ""):
                    break
        emkost = (str(tank) if tank not in (None, "") else None) or pl.container
        # Метка партии: нормальный номер (есть цифра, без времени) — как есть;
        # иначе сорт + ёмкость; в крайнем случае #id.
        b = (pl.batch_number or "").strip()
        good_batch = bool(b) and any(c.isdigit() for c in b) and ":" not in b and len(b) <= 14
        if good_batch:
            batch_label = b
        else:
            parts = [p for p in [pl.variety, emkost] if p]
            batch_label = " · ".join(parts) if parts else f"#{pl.id}"
        for d in devs:
            dir_txt = {"below": "ниже нормы", "above": "выше нормы"}.get(d.get("direction"), "не соответствует")
            rows.append({
                "партия": batch_label,
                "сорт": pl.variety,
                "ёмкость": emkost,
                "цех": pl.container,
                "показатель": d["indicator"],
                "значение": d.get("value"),
                "ед": d.get("unit", ""),
                "норма": d.get("norm"),
                "направление": dir_txt,
                "отклонение_пр": d.get("deviation_pct"),
            })
    return rows


async def run_daily_digest(db, target_date=None, triggered="manual"):
    """Сформировать сводку за день. Возвращает объект DailyDigest."""
    from app.crud import integration_config as ci
    from app.services.external_integration import (
        ExternalSystemConfig, import_odata_results_from_1c, import_odata_sanitation_from_1c)
    from app.services import ai_analysis, ai_agent
    from app.models import DailyDigest, User

    sched = get_or_create_schedule(db)
    if target_date is None:
        today_msk = msk_now().date()
        target_date = (today_msk - timedelta(days=1)) if sched.day_mode == "yesterday" else today_msk
    df = target_date.isoformat()
    # Импорт всегда захватывает последние 3 дня (целевой день + 2 предыдущих),
    # чтобы не было пробелов в данных и в проверке просрочки санитарии.
    import_from = (target_date - timedelta(days=2)).isoformat()
    import_to = df
    status, err, import_info = "ok", None, {}

    cfg = ci.get_by_name(db, "1c")
    urow = db.query(User).order_by(User.id).first()
    uid = urow.id if urow else 1

    import_info["window"] = {"from": import_from, "to": import_to}
    if cfg:
        conf = ExternalSystemConfig(base_url=cfg.base_url, username=cfg.username,
                                    password=cfg.password, verify=False, timeout=180)
        try:
            r = await import_odata_results_from_1c(db, conf, import_from, import_to, user_id=uid)
            import_info["results"] = {k: r.get(k) for k in ("documents", "reports_created", "reports_updated", "values")}
        except Exception as e:
            status = "partial"; err = f"результаты: {e}"
            logger.warning("Сводка: импорт результатов не удался: %s", e)
        try:
            s = await import_odata_sanitation_from_1c(db, conf, import_from, import_to)
            import_info["sanitation"] = {k: s.get(k) for k in ("total", "created", "updated")}
        except Exception as e:
            status = "partial"; err = (err + "; " if err else "") + f"санитария: {e}"
            logger.warning("Сводка: импорт санитарии не удался: %s", e)
    else:
        status, err = "partial", "Нет сохранённой конфигурации 1С"

    analytics = ai_analysis.build_period_analytics(db, date_from=target_date, date_to=target_date)

    summary = ""
    try:
        ag = ai_agent.run_period_agent(db, analytics)
        if ag.get("model_configured"):
            summary = ag.get("text") or ""
        else:
            summary = "(модель не подключена — доступны только цифры сводки)"
    except Exception as e:
        summary = f"(ошибка разбора агента: {e})"
        logger.warning("Сводка: разбор агента не удался: %s", e)

    released, not_released = compute_released(db, target_date)

    # Все отклонения показателей за день (партия, сорт, ёмкость, показатель, отклонение)
    try:
        deviation_rows = compute_deviation_rows(db, target_date)
    except Exception as e:
        deviation_rows = []
        logger.warning("Сводка: список отклонений не собран: %s", e)

    # Санитария: просроченные/невыполненные мероприятия на дату сводки
    sanitation_overdue = []
    try:
        from app.services.sanitation_planner import compute_sanitation_compliance
        sanitation_overdue = compute_sanitation_compliance(db, target_date).get("overdue", [])
    except Exception as e:
        logger.warning("Сводка: планировщик санитарии не сработал: %s", e)

    dig = db.query(DailyDigest).filter(DailyDigest.digest_date == target_date).first()
    if not dig:
        dig = DailyDigest(digest_date=target_date)
        db.add(dig)
    dig.created_at = datetime.utcnow()
    dig.triggered_by = triggered
    dig.reports_count = analytics.get("reports_count") or 0
    dig.deviations_count = analytics.get("deviations_count") or 0
    dig.reports_with_deviations = analytics.get("reports_with_deviations") or 0
    dig.released_count = len(released)
    dig.not_released_count = len(not_released)
    dig.released_batches = json.dumps(released, ensure_ascii=False)
    dig.not_released_batches = json.dumps(not_released, ensure_ascii=False)
    dig.sanitation_overdue_count = len(sanitation_overdue)
    dig.sanitation_overdue = json.dumps(sanitation_overdue, ensure_ascii=False)
    dig.deviation_rows = json.dumps(deviation_rows, ensure_ascii=False)
    dig.summary = summary
    dig.status = status
    dig.error = err
    dig.import_info = json.dumps(import_info, ensure_ascii=False, default=str)[:4000]
    db.commit()
    db.refresh(dig)

    sched.last_status = status
    sched.last_run_at = datetime.utcnow()
    db.commit()
    logger.info("Сводка за %s готова: отчётов=%s отклонений=%s допущено=%s не допущено=%s",
                df, dig.reports_count, dig.deviations_count, dig.released_count, dig.not_released_count)
    return dig


# ==================== Планировщик (фоновый поток) ====================

_scheduler_started = False


def start_scheduler():
    """Запустить фоновый поток планировщика (идемпотентно)."""
    global _scheduler_started
    if _scheduler_started:
        return
    import threading
    _scheduler_started = True
    threading.Thread(target=_scheduler_loop, name="digest-scheduler", daemon=True).start()
    logger.info("Планировщик ежедневной сводки запущен")


def _scheduler_loop():
    import time as _time
    import asyncio
    from app.core.database import SessionLocal
    while True:
        try:
            db = SessionLocal()
            try:
                sched = get_or_create_schedule(db)
                if getattr(sched, "agents_enabled", True) and sched.enabled and sched.run_time:
                    now = msk_now()  # московское время
                    try:
                        hh, mm = [int(x) for x in str(sched.run_time).split(":")]
                    except Exception:
                        hh, mm = 7, 0
                    due = (now.hour, now.minute) >= (hh, mm)
                    if due and sched.last_run_date != now.date():
                        target = (now.date() - timedelta(days=1)) if sched.day_mode == "yesterday" else now.date()
                        logger.info("Автозапуск ежедневной сводки за %s", target)
                        try:
                            asyncio.run(run_daily_digest(db, target, "schedule"))
                        finally:
                            sched.last_run_date = now.date()
                            db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.warning("Планировщик сводки: %s", e)
        _time.sleep(60)
