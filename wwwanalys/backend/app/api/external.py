from fastapi import APIRouter, Depends, HTTPException, status, Header, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.deps import get_db
from app.core.config import settings
from app.crud import analysis_type as crud_template
from app.schemas import AnalysisTypeCreate, AnalysisTypeUpdate
from fastapi.security import APIKeyHeader

router = APIRouter()

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)


def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    return api_key


# ---- Схемы для интеграции с 1С ----

class OneCConnectionConfig(BaseModel):
    """Конфигурация подключения к 1С."""
    base_url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30


class OneCImportRequest(BaseModel):
    """Запрос на импорт показателей из 1С."""
    connection: OneCConnectionConfig
    endpoint: str = "/api/v1/indicators"
    field_mapping: Optional[Dict[str, str]] = None
    skip_duplicates: bool = True


class OneCImportResponse(BaseModel):
    """Ответ на импорт показателей из 1С."""
    status: str
    total: int = 0
    created: int = 0
    skipped: int = 0
    errors: List[Dict[str, Any]] = []
    timestamp: str


class OneCTestConnectionRequest(BaseModel):
    """Запрос на проверку подключения к 1С."""
    connection: OneCConnectionConfig


class OneCTestConnectionResponse(BaseModel):
    """Ответ на проверку подключения к 1С."""
    status: str
    message: str
    timestamp: str


# ---- Эндпоинты ----

@router.post("/sync-templates")
def sync_templates(
    templates_data: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Синхронизация шаблонов из внешней ERP системы
    Защита: статичный API-ключ в Header `X-API-KEY`
    """
    try:
        for template_data in templates_data:
            # Проверяем, существует ли шаблон
            existing_template = db.query(crud_template.AnalysisType).filter(
                crud_template.AnalysisType.name == template_data["name"]
            ).first()

            if existing_template:
                # Обновляем существующий шаблон
                update_data = AnalysisTypeUpdate(
                    name=template_data.get("name", existing_template.name),
                    description=template_data.get("description")
                )
                crud_template.update_template(db, existing_template.id, update_data)
            else:
                # Создаем новый шаблон
                create_data = AnalysisTypeCreate(
                    name=template_data["name"],
                    description=template_data.get("description")
                )
                crud_template.create_template(db, create_data, user_id=1)  # ID системного пользователя

        return {"message": f"Successfully synced {len(templates_data)} templates"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/1c/test-connection", response_model=OneCTestConnectionResponse)
async def test_1c_connection(
    request: OneCTestConnectionRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Проверить подключение к 1С Предприятие.
    
    Пример запроса:
    {
        "connection": {
            "base_url": "http://1c-server:8080",
            "api_key": "your-api-key",
            "timeout": 30
        }
    }
    """
    from app.services.external_integration import OneCIntegrationService
    
    config = request.connection
    service = OneCIntegrationService(
        base_url=config.base_url,
        api_key=config.api_key,
        username=config.username,
        password=config.password,
        timeout=config.timeout,
    )
    
    try:
        result = await service.test_connection()
        return OneCTestConnectionResponse(**result)
    finally:
        await service.close()


@router.post("/1c/import-indicators", response_model=OneCImportResponse)
async def import_indicators_from_1c(
    request: OneCImportRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Импортировать справочник показателей из 1С Предприятие.
    
    Пример запроса:
    {
        "connection": {
            "base_url": "http://1c-server:8080",
            "api_key": "your-api-key"
        },
        "endpoint": "/api/v1/indicators",
        "field_mapping": {
            "name": "Наименование",
            "unit": "ЕдиницаИзмерения",
            "data_type": "ТипДанных",
            "description": "Описание",
            "category": "Категория"
        },
        "skip_duplicates": true
    }
    
    Поля field_mapping (опционально):
    - Используется для маппинга полей из 1С в локальные поля
    - Если не указано, используется маппинг по умолчанию
    """
    from app.services.external_integration import (
        import_indicators_from_1c,
        ExternalSystemConfig,
    )
    
    config = ExternalSystemConfig(
        base_url=request.connection.base_url,
        api_key=request.connection.api_key,
        username=request.connection.username,
        password=request.connection.password,
        timeout=request.connection.timeout,
    )
    
    try:
        result = await import_indicators_from_1c(
            db=db,
            config=config,
            endpoint=request.endpoint,
            field_mapping=request.field_mapping,
            skip_duplicates=request.skip_duplicates,
        )
        
        return OneCImportResponse(
            status="success" if not result["errors"] else "partial",
            **result,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}",
        )


@router.get("/1c/indicators")
async def fetch_indicators_from_1c(
    base_url: str,
    api_key: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    endpoint: str = "/api/v1/indicators",
    api_key_header: str = Depends(get_api_key),
):
    """
    Получить список показателей из 1С без сохранения в БД.
    Полезно для предпросмотра данных перед импортом.
    
    Параметры:
    - base_url: URL сервера 1С
    - api_key: API-ключ (если используется)
    - username/password: Учётные данные (если используется Basic Auth)
    - endpoint: API-эндпоинт для получения показателей
    """
    from app.services.external_integration import OneCIntegrationService
    
    service = OneCIntegrationService(
        base_url=base_url,
        api_key=api_key,
        username=username,
        password=password,
    )
    
    try:
        indicators = await service.fetch_indicators_from_1c(endpoint)
        return {
            "status": "success",
            "count": len(indicators),
            "indicators": indicators,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch indicators: {str(e)}",
        )
    finally:
        await service.close()
