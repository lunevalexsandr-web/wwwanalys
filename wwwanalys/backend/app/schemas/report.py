from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime


class IndicatorValue(BaseModel):
    indicator_id: int
    value: Union[float, str]
    is_normal: Optional[bool] = None
    day: Optional[int] = None


class ReportCreate(BaseModel):
    template_id: int
    batch_number: str
    variety: Optional[str] = None
    container: Optional[str] = None
    values: List[IndicatorValue]
    plan_item_id: Optional[int] = None


class IndicatorValueReport(BaseModel):
    id: int
    indicator_id: int
    value: Optional[float] = None
    text_value: Optional[str] = None
    day: Optional[int] = None
    is_normal: bool

    class Config:
        from_attributes = True


class Report(BaseModel):
    id: int
    batch_number: str
    variety: Optional[str] = None
    container: Optional[str] = None
    analysis_type_id: int
    started_at: datetime
    status: str
    notes: Optional[str] = None
    values: List[IndicatorValueReport] = []
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_alias(cls, obj):
        from app.models import IndicatorValue as IndicatorValueModel

        data = {
            'id': obj.id,
            'batch_number': obj.batch_number,
            'variety': getattr(obj, 'variety', None),
            'container': getattr(obj, 'container', None),
            'analysis_type_id': obj.analysis_type_id,
            'started_at': obj.started_at,
            'status': obj.status.value if hasattr(obj.status, 'value') else obj.status,
            'notes': obj.notes,
            'created_by': obj.created_by,
            'values': [
                IndicatorValueReport(
                    id=v.id,
                    indicator_id=v.indicator_id,
                    value=v.value,
                    text_value=v.text_value,
                    day=getattr(v, 'day', None),
                    is_normal=v.is_normal
                ) for v in obj.indicator_values
            ] if hasattr(obj, 'indicator_values') and obj.indicator_values else []
        }
        return cls(**data)