from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class TemplateIndicator(Base):
    """Связь шаблона с показателем из справочника."""
    __tablename__ = "template_indicators"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("analysis_types.id", ondelete="CASCADE"))
    indicator_id = Column(Integer, ForeignKey("indicator_library.id", ondelete="CASCADE"))
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    norm_text = Column(String, nullable=True)  # нечисловая (эталонная) норма из 1С
    sort_order = Column(Integer, default=0)

    # Новые поля
    is_custom = Column(Boolean, default=False)              # Пользовательский показатель (не из справочника)
    template_notes = Column(Text, nullable=True)             # Примечания к показателю в шаблоне
    external_id = Column(String(255), nullable=True, index=True)  # ID связи показателя в шаблоне из внешней системы (1С)

    # Связи
    template = relationship("AnalysisType", back_populates="template_indicators")
    indicator_ref = relationship("IndicatorLibrary", back_populates="template_indicators")