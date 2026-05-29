from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class IndicatorValue(Base):
    __tablename__ = "indicator_values"
    
    id = Column(Integer, primary_key=True, index=True)
    process_log_id = Column(Integer, ForeignKey("process_logs.id"))
    indicator_id = Column(Integer, ForeignKey("indicators.id"))
    value = Column(Float)
    measured_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(String)
    
    # Связь с моделью ProcessLog
    process_log = relationship("ProcessLog", back_populates="indicator_values")
    
    # Связь с моделью Indicator
    indicator = relationship("Indicator", back_populates="values")