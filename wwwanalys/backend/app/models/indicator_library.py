from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class IndicatorLibrary(Base):
    """Глобальный справочник показателей."""
    __tablename__ = "indicator_library"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    unit = Column(String, nullable=True)
    data_type = Column(String(20), default="number")
    options = Column(Text)  # JSON-строка для SELECT типа

    # Новые поля
    description = Column(Text, nullable=True)           # Подробное описание
    category = Column(String(50), nullable=True)         # Категория: quality, safety, performance
    is_required = Column(Boolean, default=False)         # Обязательный показатель
    default_value = Column(String, nullable=True)        # Значение по умолчанию
    validation_rules = Column(Text, nullable=True)       # Правила валидации в JSON
    created_by = Column(Integer, nullable=True)          # ID пользователя, создавшего показатель
    created_at = Column(DateTime, default=datetime.utcnow)
    external_id = Column(String(255), nullable=True, unique=True, index=True)  # ID показателя из внешней системы (1С)

    # Связь с TemplateIndicator
    template_indicators = relationship("TemplateIndicator", back_populates="indicator_ref")
