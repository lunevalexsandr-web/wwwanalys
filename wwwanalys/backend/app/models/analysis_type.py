from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class AnalysisType(Base):
    __tablename__ = "analysis_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    
    # Связь с моделью User
    creator = relationship("User", back_populates="created_analysis_types")
    
    # Связь с моделью Indicator
    indicators = relationship("Indicator", back_populates="analysis_type")
    
    # Связь с моделью ProcessLog
    process_logs = relationship("ProcessLog", back_populates="analysis_type")