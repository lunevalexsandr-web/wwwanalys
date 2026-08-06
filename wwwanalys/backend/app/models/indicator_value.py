from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime, timezone

class IndicatorValue(Base):
    __tablename__ = "indicator_values"
    
    id = Column(Integer, primary_key=True, index=True)
    process_log_id = Column(Integer, ForeignKey("process_logs.id"))
    indicator_id = Column(Integer, ForeignKey("indicator_library.id"))
    value = Column(Float, nullable=True)
    text_value = Column(String, nullable=True)
    day = Column(Integer, nullable=True)  # день измерения (для показателей с расписанием)
    is_normal = Column(Boolean, default=True)
    measured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(String)
    
    # Связь с моделью ProcessLog
    process_log = relationship("ProcessLog", back_populates="indicator_values")
    
    # Связь с моделью IndicatorLibrary
    indicator = relationship("IndicatorLibrary")
