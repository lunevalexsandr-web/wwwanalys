from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime, timezone


class AnalysisType(Base):
    __tablename__ = "analysis_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    external_id = Column(String(255), nullable=True, unique=True, index=True)  # ID шаблона из внешней системы (1С)

    # Связь с моделью User
    creator = relationship("User", back_populates="created_analysis_types")
    
    # Связь с моделью Indicator (прямые индикаторы, устаревший подход)
    indicators = relationship("Indicator", back_populates="analysis_type")
    
    # Связь с TemplateIndicator (новый подход через справочник)
    template_indicators = relationship("TemplateIndicator", back_populates="template", cascade="all, delete-orphan")
    
    # Связь с моделью ProcessLog
    process_logs = relationship("ProcessLog", back_populates="analysis_type")