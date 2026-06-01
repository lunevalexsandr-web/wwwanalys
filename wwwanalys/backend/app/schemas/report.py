from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .process_log import ProcessLog as ProcessLogSchema, IndicatorValueCreate
from .analysis_type import Indicator as IndicatorSchema

class IndicatorValue(BaseModel):
    indicator_id: int
    value: float
    is_normal: Optional[bool] = None

class ReportCreate(BaseModel):
    template_id: int
    batch_number: str
    values: List[IndicatorValue]

class Report(ProcessLogSchema):
    values: List[IndicatorSchema] = []
    
    class Config:
        from_attributes = True

class IndicatorValueReport(BaseModel):
    id: int
    indicator_id: int
    value: float
    is_normal: bool
    
    class Config:
        from_attributes = True