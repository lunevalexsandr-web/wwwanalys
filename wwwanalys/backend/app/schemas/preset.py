from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json


class PresetIndicatorBase(BaseModel):
    indicator_id: int
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    sort_order: int = 0
    is_required: bool = False


class PresetIndicatorCreate(PresetIndicatorBase):
    pass


class PresetIndicatorDetail(PresetIndicatorBase):
    id: int
    preset_id: int
    indicator_name: str = ""
    indicator_unit: str = ""
    indicator_data_type: str = "number"
    indicator_options: Optional[List[str]] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_ref(cls, preset_indicator):
        """Сформировать из ORM с подгрузкой данных из справочника."""
        options = None
        lib_ind = preset_indicator.indicator_ref
        if lib_ind:
            if lib_ind.options:
                try:
                    options = json.loads(lib_ind.options)
                except (json.JSONDecodeError, TypeError):
                    options = None
            return cls(
                id=preset_indicator.id,
                preset_id=preset_indicator.preset_id,
                indicator_id=preset_indicator.indicator_id,
                min_value=preset_indicator.min_value,
                max_value=preset_indicator.max_value,
                sort_order=preset_indicator.sort_order,
                is_required=bool(preset_indicator.is_required),
                indicator_name=lib_ind.name,
                indicator_unit=lib_ind.unit or "",
                indicator_data_type=lib_ind.data_type or "number",
                indicator_options=options,
            )
        return cls(
            id=preset_indicator.id,
            preset_id=preset_indicator.preset_id,
            indicator_id=preset_indicator.indicator_id,
            min_value=preset_indicator.min_value,
            max_value=preset_indicator.max_value,
            sort_order=preset_indicator.sort_order,
            is_required=bool(preset_indicator.is_required),
        )


class PresetBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None


class PresetCreate(PresetBase):
    indicators: List[PresetIndicatorCreate] = []


class Preset(PresetBase):
    id: int
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    indicators: List[PresetIndicatorDetail] = []

    class Config:
        from_attributes = True


class PresetListItem(BaseModel):
    """Краткая информация о пресете для списка."""
    id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    indicators_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True