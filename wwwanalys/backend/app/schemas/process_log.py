from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.process_log import Status

class ProcessLogBase(BaseModel):
    analysis_type_id: int
    status: Status = Status.PENDING
    notes: Optional[str] = None

class ProcessLogCreate(ProcessLogBase):
    pass

class ProcessLogUpdate(BaseModel):
    status: Optional[Status] = None
    notes: Optional[str] = None

class IndicatorValueBase(BaseModel):
    indicator_id: int
    value: float
    notes: Optional[str] = None

class IndicatorValueCreate(IndicatorValueBase):
    pass

class IndicatorValue(IndicatorValueBase):
    id: int
    process_log_id: int
    measured_at: datetime
    
    class Config:
        orm_mode = True

class ProcessLog(ProcessLogBase):
    id: int
    user_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    indicator_values: List[IndicatorValue] = []
    
    class Config:
        orm_mode = True