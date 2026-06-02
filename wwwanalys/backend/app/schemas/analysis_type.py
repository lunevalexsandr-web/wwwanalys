from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import json

class DataType(str, Enum):
    NUMBER = "number"
    TEXT = "text"
    SELECT = "select"

class IndicatorBase(BaseModel):
    name: str
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    data_type: DataType = DataType.NUMBER
    options: Optional[List[str]] = None  # Список вариантов для SELECT типа

class IndicatorCreate(IndicatorBase):
    @field_validator('data_type', mode='before')
    @classmethod
    def parse_data_type(cls, v):
        """Конвертирует строку в DataType enum"""
        if isinstance(v, str):
            try:
                return DataType(v)
            except ValueError:
                return DataType.NUMBER
        return v
    
    @field_validator('options', mode='before')
    @classmethod
    def parse_options_input(cls, v):
        """Парсит список опций из разных форматов"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else None
            except json.JSONDecodeError:
                # Если это не JSON, пробуем разделить по запятой
                return [x.strip() for x in v.split(',') if x.strip()]
        return v

class Indicator(IndicatorBase):
    id: int
    analysis_type_id: int
    
    class Config:
        from_attributes = True
    
    @field_validator('options', mode='before')
    @classmethod
    def parse_options(cls, v):
        """Парсит JSON-строку options в список"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

class AnalysisTypeBase(BaseModel):
    name: str
    description: Optional[str] = None

class AnalysisTypeCreate(AnalysisTypeBase):
    indicators: List[IndicatorCreate] = []

class AnalysisTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    indicators: Optional[List[IndicatorCreate]] = None

class AnalysisType(AnalysisTypeBase):
    id: int
    created_at: datetime
    created_by: int
    is_active: bool
    indicators: List[Indicator] = []
    
    class Config:
        from_attributes = True
