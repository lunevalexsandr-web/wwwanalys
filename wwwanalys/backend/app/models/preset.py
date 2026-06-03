from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime


class Preset(Base):
    """Предустановленный набор показателей (пресет)."""
    __tablename__ = "presets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # quality, safety, performance, chemical, physical
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Связи
    creator = relationship("User", back_populates="created_presets")
    indicators = relationship("PresetIndicator", back_populates="preset", cascade="all, delete-orphan")


class PresetIndicator(Base):
    """Показатель в составе пресета."""
    __tablename__ = "preset_indicators"

    id = Column(Integer, primary_key=True, index=True)
    preset_id = Column(Integer, ForeignKey("presets.id", ondelete="CASCADE"))
    indicator_id = Column(Integer, ForeignKey("indicator_library.id", ondelete="CASCADE"))
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    sort_order = Column(Integer, default=0)
    is_required = Column(Integer, default=0)  # 0/1 — обязательность в пресете

    # Связи
    preset = relationship("Preset", back_populates="indicators")
    indicator_ref = relationship("IndicatorLibrary")