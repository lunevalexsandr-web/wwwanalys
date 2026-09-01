"""План лабораторных анализов из 1С (РегистрСведений _ПланированиеЛабораторныхАнализов).
1С сама формирует план и ведёт статус выполнения — мы импортируем и показываем."""
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Index
from datetime import datetime
from app.core.database import Base


class AnalysisPlanEntry(Base):
    """Одна запись плана: объект контроля + серия/смена + статус выполнения."""
    __tablename__ = "analysis_plan_1c"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)   # md5 составного ключа

    period = Column(DateTime)                               # момент записи плана
    shift_date = Column(Date, index=True)                   # ДатаСмены
    shift_no = Column(String)                               # НомерСмены

    control_object_key = Column(String)
    control_object_name = Column(String)                   # Description объекта контроля
    periodicity = Column(String)                            # enum периодичности из справочника
    analysis_type_key = Column(String)
    analysis_type_name = Column(String)                    # название типового анализа (шаблона)

    series_key = Column(String)
    batch_number = Column(String)                          # серия/партия (Description)
    nomenclature_key = Column(String)
    variety = Column(String)                                # номенклатура/сорт (Description)

    status = Column(String)                                 # СтатусАнализа: ОжидаетОбработки | Обработан
    done = Column(Boolean, default=False)                  # выполнен (есть ДокументАнализа)
    analysis_doc_key = Column(String)

    imported_at = Column(DateTime, default=datetime.utcnow)


Index("ix_analysis_plan_1c_shift_status", AnalysisPlanEntry.shift_date, AnalysisPlanEntry.status)
