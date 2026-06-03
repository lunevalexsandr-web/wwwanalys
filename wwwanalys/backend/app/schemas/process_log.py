from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class StatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class IndicatorValueCreate(BaseModel):
    indicator_id: int
    value: float

class IndicatorValueSchema(BaseModel):
    indicator_id: int
    value: float
    is_normal: Optional[bool] = None

    class Config:
        from_attributes = True

class ProcessLogBase(BaseModel):
    batch_number: str
    analysis_type_id: int
    status: StatusEnum = StatusEnum.PENDING
    notes: Optional[str] = None

class ProcessLogCreate(ProcessLogBase):
    indicator_values: List[IndicatorValueCreate] = []

class ProcessLogUpdate(BaseModel):
    status: Optional[StatusEnum] = None
    notes: Optional[str] = None

class ProcessLog(ProcessLogBase):
    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True