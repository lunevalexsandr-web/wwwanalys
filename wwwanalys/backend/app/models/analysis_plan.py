from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime, timezone


class AnalysisPlan(Base):
    """План анализов на конкретную дату."""
    __tablename__ = "analysis_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    plan_date = Column(Date, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_completed = Column(Boolean, default=False)
    
    # Связи
    creator = relationship("User", back_populates="analysis_plans")
    plan_items = relationship("PlanItem", back_populates="plan", cascade="all, delete-orphan")


class PlanItem(Base):
    """Элемент плана - какой шаблон заполнять."""
    __tablename__ = "plan_items"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("analysis_plans.id", ondelete="CASCADE"))
    template_id = Column(Integer, ForeignKey("analysis_types.id"), nullable=False)
    batch_number = Column(String, nullable=True)  # Предзаполненный номер партии
    sort_order = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_report_id = Column(Integer, ForeignKey("process_logs.id"), nullable=True)
    
    # Связи
    plan = relationship("AnalysisPlan", back_populates="plan_items")
    template = relationship("AnalysisType")
    report = relationship("ProcessLog")