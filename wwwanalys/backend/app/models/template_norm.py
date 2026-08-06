"""Матрица норм шаблона: норма зависит от (показатель, день, сорт, тара, объект).

Наполняется из 1С (ТЧ Нормативы + ПоказателиАнализа). Пустое (NULL) значение
измерения означает «любой» — используется при подборе нормы с фолбэком.
Существующее поведение (TemplateIndicator.min/max/norm_text) не затрагивает —
это отдельный слой (Этап 1: только данные).
"""
from sqlalchemy import Column, Integer, Float, String, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class TemplateNorm(Base):
    __tablename__ = "template_norms"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("analysis_types.id", ondelete="CASCADE"), index=True)
    indicator_id = Column(Integer, ForeignKey("indicator_library.id", ondelete="CASCADE"), index=True)

    day = Column(Integer, nullable=True)            # NULL = любой день; 0,15,30… — конкретный
    variety_key = Column(String(255), nullable=True) # GUID сорта (Характеристика номенклатуры)
    container = Column(String(50), nullable=True)    # тара/линия: КЕГ/Стекло/ПЭТ/Стекло2
    object_key = Column(String(255), nullable=True)  # GUID объекта анализа/отбора
    object_name = Column(String(255), nullable=True) # резолв имени объекта (если доступен)

    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    norm_text = Column(String, nullable=True)        # нечисловая норма

    source = Column(String(20), nullable=True)       # 'normativy' | 'schedule'

    template = relationship("AnalysisType")
    indicator_ref = relationship("IndicatorLibrary")


Index("ix_template_norms_lookup", TemplateNorm.template_id, TemplateNorm.indicator_id)
