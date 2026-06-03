from pydantic import BaseModel
from typing import Optional


class TemplateIndicatorBase(BaseModel):
    indicator_id: int
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    sort_order: int = 0
    is_custom: bool = False
    template_notes: Optional[str] = None


class TemplateIndicatorCreate(TemplateIndicatorBase):
    pass


class TemplateIndicator(TemplateIndicatorBase):
    id: int
    template_id: int

    class Config:
        from_attributes = True