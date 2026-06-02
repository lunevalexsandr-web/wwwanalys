from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime
from .analysis_type import Indicator as IndicatorSchema

class IndicatorValue(BaseModel):
    indicator_id: int
    value: Union[float, str]
    is_normal: Optional[bool] = None

class ReportCreate(BaseModel):
    template_id: int
    batch_number: str
    values: List[IndicatorValue]

class Report(BaseModel):
    id: int
    batch_number: str
    analysis_type_id: int
    started_at: datetime
    status: str
    notes: Optional[str] = None
    values: List[IndicatorSchema] = []
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_with_alias(cls, obj):
        data = {
            'id': obj.id,
            'batch_number': obj.batch_number,
            'analysis_type_id': obj.analysis_type_id,
            'started_at': obj.started_at,
            'status': obj.status.value if hasattr(obj.status, 'value') else obj.status,
            'notes': obj.notes,
            'values': []
        }
        return cls(**data)

class IndicatorValueReport(BaseModel):
    id: int
    indicator_id: int
    value: Optional[float] = None
    text_value: Optional[str] = None
    is_normal: bool
    
    class Config:
        from_attributes = True
