"""Справочник объектов анализа/отбора (из 1С Catalog__ОбъектыАнализа)."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone

from app.core.database import Base


class AnalysisObject(Base):
    __tablename__ = "analysis_objects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    code = Column(String(100), nullable=True)
    external_id = Column(String(255), nullable=True, unique=True, index=True)  # Ref_Key из 1С
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
