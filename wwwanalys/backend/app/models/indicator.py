from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Indicator(Base):
    __tablename__ = "indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    unit = Column(String)
    min_value = Column(Float)
    max_value = Column(Float)
    analysis_type_id = Column(Integer, ForeignKey("analysis_types.id"))
    
    # Связь с моделью AnalysisType
    analysis_type = relationship("AnalysisType", back_populates="indicators")
    
    # Связь с моделью IndicatorValue
    values = relationship("IndicatorValue", back_populates="indicator")