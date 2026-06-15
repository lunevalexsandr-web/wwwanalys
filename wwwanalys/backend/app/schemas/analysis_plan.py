from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, datetime


class PlanItemBase(BaseModel):
    template_id: int
    batch_number: Optional[str] = None
    sort_order: int = 0


class PlanItemCreate(PlanItemBase):
    pass


class PlanItemDetail(PlanItemBase):
    """Детальная информация об элементе плана."""
    id: int
    plan_id: int
    is_completed: bool = False
    template_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class PlanItemUpdate(BaseModel):
    batch_number: Optional[str] = None
    is_completed: Optional[bool] = None
    completed_report_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class AnalysisPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    plan_date: date


class AnalysisPlanCreate(AnalysisPlanBase):
    plan_items: List[PlanItemCreate] = []


class AnalysisPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    plan_date: Optional[date] = None
    is_completed: Optional[bool] = None


class AnalysisPlan(AnalysisPlanBase):
    id: int
    created_by: int
    created_at: datetime
    is_completed: bool
    plan_items: List[PlanItemDetail] = []
    
    class Config:
        from_attributes = True


# Схемы для фронтенда - ответ с полной информацией о шаблоне
class PlanItemTemplateInfo(BaseModel):
    """Информация о шаблоне внутри плана."""
    id: int
    name: str
    description: Optional[str] = None
    template_indicators: List[dict] = []
    
    class Config:
        from_attributes = True


class PlanItemResponse(PlanItemBase):
    """Элемент плана для ответа API с полной информацией о шаблоне."""
    id: int
    plan_id: int
    is_completed: bool = False
    template: Optional[PlanItemTemplateInfo] = None
    
    class Config:
        from_attributes = True
