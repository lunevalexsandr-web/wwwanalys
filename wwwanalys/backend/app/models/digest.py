from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Text
from datetime import datetime
from app.core.database import Base


class DigestSchedule(Base):
    """Настройки ежедневной автозадачи агента (singleton, id=1)."""
    __tablename__ = "digest_schedule"

    id = Column(Integer, primary_key=True, index=True)
    agents_enabled = Column(Boolean, default=True)    # ГЛАВНЫЙ рубильник всех агентов
    enabled = Column(Boolean, default=False)          # включён ли автозапуск сводки
    run_time = Column(String, default="07:00")        # время запуска HH:MM (по времени сервера)
    day_mode = Column(String, default="yesterday")    # yesterday | today
    last_run_date = Column(Date)                       # дата последнего авто-запуска
    last_status = Column(String)                       # ok | partial | error
    last_run_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailyDigest(Base):
    """Ежедневная сводка: результаты за день, отклонения, допуск партий, разбор агента."""
    __tablename__ = "daily_digests"

    id = Column(Integer, primary_key=True, index=True)
    digest_date = Column(Date, index=True)            # за какой день
    created_at = Column(DateTime, default=datetime.utcnow)
    triggered_by = Column(String)                     # schedule | manual

    reports_count = Column(Integer, default=0)
    deviations_count = Column(Integer, default=0)
    reports_with_deviations = Column(Integer, default=0)
    released_count = Column(Integer, default=0)
    not_released_count = Column(Integer, default=0)

    released_batches = Column(Text)                   # JSON: [{batch, variety, value}]
    not_released_batches = Column(Text)               # JSON
    sanitation_overdue_count = Column(Integer, default=0)  # просроченных сан. мероприятий
    sanitation_overdue = Column(Text)                 # JSON: просроченные/невыполненные мероприятия
    deviation_rows = Column(Text)                     # JSON: отклонения (партия, сорт, ёмкость, показатель, отклонение)
    summary = Column(Text)                            # разбор агента (что исправить)
    status = Column(String)                           # ok | partial | error
    error = Column(Text)
    import_info = Column(Text)                        # JSON: что импортировано
