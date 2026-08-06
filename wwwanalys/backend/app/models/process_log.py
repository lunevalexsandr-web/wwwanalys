from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime, timezone
from enum import Enum as PyEnum

class Status(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessLog(Base):
    __tablename__ = "process_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_number = Column(String, index=True)  # = СерияНоменклатуры2 (номер серии в 1С)
    series_key = Column(String, nullable=True, index=True)  # СерияНоменклатуры (GUID из 1С)
    variety = Column(String, nullable=True, index=True)  # сорт — ключ к техкарте (RAG)
    container = Column(String, nullable=True)  # тара/линия розлива: КЕГ/Стекло/ПЭТ/Стекло2
    object_key = Column(String, nullable=True)  # объект отбора (GUID из 1С) — для подбора нормы
    external_id = Column(String(255), nullable=True, index=True)  # регистратор/документ 1С (для синхронизации)
    analysis_type_id = Column(Integer, ForeignKey("analysis_types.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(Status), default=Status.PENDING)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    notes = Column(String)
    
    # Связь с моделью AnalysisType
    analysis_type = relationship("AnalysisType", back_populates="process_logs")
    
    # Связь с моделью User
    creator = relationship("User", back_populates="process_logs")
    
    # Связь с моделью IndicatorValue
    indicator_values = relationship("IndicatorValue", back_populates="process_log")