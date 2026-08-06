from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VarietyBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None
    is_active: bool = True


class VarietyCreate(VarietyBase):
    pass


class VarietyUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None
    is_active: Optional[bool] = None


class Variety(VarietyBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
