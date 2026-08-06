"""Pydantic-схемы для конфигурации внешних интеграций."""
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class IntegrationConfigBase(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = False
    is_active: bool = True
    endpoint: Optional[str] = None
    indicators_endpoint: Optional[str] = None
    templates_endpoint: Optional[str] = None
    plans_endpoint: Optional[str] = None
    varieties_endpoint: Optional[str] = None
    options_endpoint: Optional[str] = None
    storage_endpoint: Optional[str] = None


class IntegrationConfigUpdate(IntegrationConfigBase):
    """Обновление конфигурации (все поля опциональны)."""
    pass


class IntegrationConfigResponse(BaseModel):
    """Ответ — конфигурация без пароля (скрыт)."""
    model_config = ConfigDict(from_attributes=True)

    name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    username: Optional[str] = None
    timeout: int = 30
    endpoint: Optional[str] = None
    indicators_endpoint: Optional[str] = None
    templates_endpoint: Optional[str] = None
    plans_endpoint: Optional[str] = None
    varieties_endpoint: Optional[str] = None
    options_endpoint: Optional[str] = None
    storage_endpoint: Optional[str] = None
    verify_ssl: bool = False
    is_active: bool = True
    updated_at: Optional[Any] = None
