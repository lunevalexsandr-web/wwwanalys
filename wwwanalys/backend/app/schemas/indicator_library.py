from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
import json


class IndicatorLibraryBase(BaseModel):
    name: str
    unit: str
    data_type: str = "number"
    options: Optional[List[str]] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_required: bool = False
    default_value: Optional[str] = None
    validation_rules: Optional[str] = None


class IndicatorLibraryCreate(IndicatorLibraryBase):
    @field_validator('data_type', mode='before')
    @classmethod
    def parse_data_type(cls, v):
        if isinstance(v, str):
            return v
        return v

    @field_validator('options', mode='before')
    @classmethod
    def parse_options_input(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else None
            except json.JSONDecodeError:
                return [x.strip() for x in v.split(',') if x.strip()]
        return v


class IndicatorLibrary(IndicatorLibraryBase):
    id: int
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_validator('options', mode='before')
    @classmethod
    def parse_options(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


# ---- Batch операции ----

class BatchCreateItem(BaseModel):
    """Один элемент для batch-создания."""
    name: str
    unit: str
    data_type: str = "number"
    options: Optional[List[str]] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_required: bool = False
    default_value: Optional[str] = None
    validation_rules: Optional[str] = None


class BatchCreateRequest(BaseModel):
    """Запрос на batch-создание показателей."""
    indicators: List[BatchCreateItem]


class BatchCreateResponse(BaseModel):
    """Ответ на batch-создание."""
    created: List[IndicatorLibrary]
    errors: List[dict] = []


class BatchUpdateItem(BaseModel):
    """Один элемент для batch-обновления."""
    id: int
    name: Optional[str] = None
    unit: Optional[str] = None
    data_type: Optional[str] = None
    options: Optional[List[str]] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_required: Optional[bool] = None
    default_value: Optional[str] = None
    validation_rules: Optional[str] = None


class BatchUpdateRequest(BaseModel):
    """Запрос на batch-обновление показателей."""
    indicators: List[BatchUpdateItem]


class BatchUpdateResponse(BaseModel):
    """Ответ на batch-обновление."""
    updated: List[IndicatorLibrary]
    errors: List[dict] = []


class BatchDeleteRequest(BaseModel):
    """Запрос на batch-удаление показателей."""
    ids: List[int]


class BatchDeleteResponse(BaseModel):
    """Ответ на batch-удаление."""
    deleted_ids: List[int]
    errors: List[dict] = []


# ---- Параметры поиска и фильтрации ----

class IndicatorLibraryFilter(BaseModel):
    """Параметры фильтрации списка показателей."""
    search: Optional[str] = None
    category: Optional[str] = None
    data_type: Optional[str] = None
    is_required: Optional[bool] = None
    skip: int = 0
    limit: int = 100