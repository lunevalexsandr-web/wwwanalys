from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class IndicatorLibraryVersionBase(BaseModel):
    indicator_id: int
    version: int = 1
    name: str
    unit: str
    data_type: str = "number"
    options: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_required: bool = False
    default_value: Optional[str] = None
    validation_rules: Optional[str] = None
    changed_by: Optional[int] = None
    change_type: str = "update"  # create | update | delete
    change_notes: Optional[str] = None


class IndicatorLibraryVersionCreate(IndicatorLibraryVersionBase):
    pass


class IndicatorLibraryVersion(IndicatorLibraryVersionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class IndicatorVersionHistory(BaseModel):
    """Для ответа API: версия + метаданные"""
    id: int
    version: int
    change_type: str
    change_notes: Optional[str] = None
    changed_by: Optional[int] = None
    created_at: datetime
    # Снапшот на тот момент
    name: str
    unit: str
    data_type: str
    options: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_required: bool
    default_value: Optional[str] = None

    class Config:
        from_attributes = True