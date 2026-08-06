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

    @field_validator('data_type', mode='before')
    @classmethod
    def parse_data_type(cls, v):
        """Конвертирует строку или enum в DataType enum"""
        if v is None:
            return DataType.NUMBER
        if isinstance(v, str):
            try:
                return DataType(v)
            except ValueError:
                return DataType.NUMBER
        return v
    
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


# Новые схемы для работы со справочником показателей
class LibraryIndicatorRef(BaseModel):
    """Ссылка на показатель из библиотеки с нормами для шаблона."""
    indicator_id: int
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    sort_order: int = 0


class TemplateIndicatorDetail(BaseModel):
    """Детальная информация о показателе в шаблоне (для ответа API)."""
    id: int
    indicator_id: int
    name: str
    unit: str
    data_type: str = "number"
    options: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    norm_text: Optional[str] = None
    sort_order: int = 0
    is_custom: bool = False
    template_notes: Optional[str] = None

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


class AnalysisTypeBase(BaseModel):
    name: str
    description: Optional[str] = None


class AnalysisTypeCreate(AnalysisTypeBase):
    # Список ссылок на показатели из библиотеки
    library_indicators: List[LibraryIndicatorRef] = []


class AnalysisTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    library_indicators: Optional[List[LibraryIndicatorRef]] = None


class AnalysisType(AnalysisTypeBase):
    id: int
    created_at: datetime
    created_by: int
    is_active: bool
    # Показатели из библиотеки (детальная информация)
    template_indicators: List[TemplateIndicatorDetail] = []
    
    class Config:
        from_attributes = True


# ---- Схемы для копирования шаблона ----
class CopyTemplateRequest(BaseModel):
    """Запрос на копирование шаблона."""
    new_name: str
    new_description: Optional[str] = None


# ---- Схемы для создания шаблона из пресета ----
class CreateFromPresetRequest(BaseModel):
    """Запрос на создание шаблона из пресета."""
    preset_id: int
    template_name: str
    template_description: Optional[str] = None