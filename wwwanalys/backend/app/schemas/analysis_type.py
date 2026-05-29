from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class IndicatorBase(BaseModel):
    name: str
    unit: str
    min_value: float
    max_value: float

class IndicatorCreate(IndicatorBase):
    pass

class Indicator(IndicatorBase):
    id: int
    analysis_type_id: int
    
    class Config:
        orm_mode = True

class AnalysisTypeBase(BaseModel):
    name: str
    description: Optional[str] = None

class AnalysisTypeCreate(AnalysisTypeBase):
    indicators: List[IndicatorCreate] = []

class AnalysisTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class AnalysisType(AnalysisTypeBase):
    id: int
    created_at: datetime
    created_by: int
    indicators: List[Indicator] = []
    
    class Config:
        orm_mode = True