from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.core.database import Base


class SanitationRecord(Base):
    """Санитарные мероприятия из 1С (РегистрСведений _ОтчётПоСменеСанитарныеМероприятия).

    Импортируется по OData; ключи 1С расшифрованы в названия через справочники.
    external_id — стабильный ключ записи регистра (для идемпотентного импорта).
    """
    __tablename__ = "sanitation_records"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # хэш составного ключа регистра

    period = Column(DateTime, index=True)          # дата/период
    shift = Column(String)                          # номер смены
    start_time = Column(DateTime)                   # время начала
    end_time = Column(DateTime)                     # время окончания

    measure_key = Column(String)                    # GUID вида мероприятия
    measure_name = Column(String)                   # название мероприятия
    line_key = Column(String)                       # GUID линии розлива
    line_name = Column(String)                      # название линии
    department_key = Column(String)                 # GUID подразделения
    department_name = Column(String)                # название подразделения
    responsible_key = Column(String)                # GUID ответственного
    responsible_name = Column(String)               # ФИО ответственного

    comment = Column(Text)                          # комментарий
    imported_at = Column(DateTime, default=datetime.utcnow)
