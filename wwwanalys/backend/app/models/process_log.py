from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
from enum import Enum as PyEnum

class Status(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessLog(Base):
    __tablename__ = "process_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_type_id = Column(Integer, ForeignKey("analysis_types.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(Status), default=Status.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(String)
    
    # Связь с моделью AnalysisType
    analysis_type = relationship("AnalysisType", back_populates="process_logs")
    
    # Связь с моделью User
    user = relationship("User", back_populates="process_logs")
    
    # Связь с моделью IndicatorValue
    indicator_values = relationship("IndicatorValue", back_populates="process_log")