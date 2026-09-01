"""Ежедневная сводка «дежурного агента»: импорт за день из 1С → отклонения →
разбор агента (что исправить) → допущенные/недопущенные партии → сохранение сводки."""
import json
import logging
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)


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
    rows = (db.query(ProcessLog.batch_number, ProcessLog.variety, IndicatorValue.text_value)
            .join(IndicatorValue, IndicatorValue.process_log_id == ProcessLog.id)
            .join(IndicatorLibrary, IndicatorLibrary.id == IndicatorValue.indicator_id)
            .filter(func.date(ProcessLog.started_at) == target_date,
                    IndicatorLibrary.name.ilike("%допуск%"))
            .all())
    released, not_released = {}, {}
    for batch, variety, val in rows:
        v = (val or "").strip().lower()
        item = {"batch": batch, "variety": variety, "value": val}
        if v == "допуск":
            released[batch] = item
        else:
            not_released[batch] = item
    return list(released.values()), list(not_released.values())


async def run_daily_digest(db, target_date=None, triggered="manual"):
    """Сформировать сводку за день. Возвращает объект DailyDigest."""
    from app.crud import integration_config as ci
    from app.services.external_integration import (
        ExternalSystemConfig, import_odata_results_from_1c, import_odata_sanitation_from_1c)
    from app.services import ai_analysis, ai_agent
    from app.models import DailyDigest, User

    sched = get_or_create_schedule(db)
    if target_date is None:
        target_date = (date.today() - timedelta(days=1)) if sched.day_mode == "yesterday" else date.today()
    df = target_date.isoformat()
    status, err, import_info = "ok", None, {}

    cfg = ci.get_by_name(db, "1c")
    urow = db.query(User).order_by(User.id).first()
    uid = urow.id if urow else 1

    if cfg:
        conf = ExternalSystemConfig(base_url=cfg.base_url, username=cfg.username,
                                    password=cfg.password, verify=False, timeout=180)
        try:
            r = await import_odata_results_from_1c(db, conf, df, df, user_id=uid)
            import_info["results"] = {k: r.get(k) for k in ("documents", "reports_created", "reports_updated", "values")}
        except Exception as e:
            status = "partial"; err = f"результаты: {e}"
            logger.warning("Сводка: импорт результатов не удался: %s", e)
        try:
            s = await import_odata_sanitation_from_1c(db, conf, df, df)
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
                if sched.enabled and sched.run_time:
                    now = datetime.now()
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
