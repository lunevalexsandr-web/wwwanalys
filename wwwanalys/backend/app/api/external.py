from fastapi import APIRouter, Depends, HTTPException, status, Header, Body, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.deps import get_db
from app.core.config import settings
from app.crud import analysis_type as crud_template
from app.schemas import AnalysisTypeCreate, AnalysisTypeUpdate
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.auth.auth import get_current_active_user
from app.models import User
from app.crud import integration_config as crud_integration
from app.schemas import IntegrationConfigUpdate, IntegrationConfigResponse

router = APIRouter()

INTEGRATION_NAME = "1c"

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    user: Optional[User] = Depends(get_current_active_user),
):
    """
    Защита external-эндпоинтов.
    Допускается либо статичный X-API-KEY, либо авторизованный пользователь (Bearer JWT).
    """
    if api_key and api_key == settings.api_key:
        return api_key
    if user is not None:
        return "bearer"
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Требуется X-API-KEY или авторизация пользователя",
    )


# ==================== Схемы для интеграции с 1С ====================

class OneCConnectionConfig(BaseModel):
    """Конфигурация подключения к 1С."""
    base_url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    endpoint: str = "/erp_24/hs/labindicators/indicators"


# --- Показатели ---

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


# --- Шаблоны ---

class OneCTemplateImportRequest(BaseModel):
    """Запрос на импорт шаблонов из 1С."""
    connection: OneCConnectionConfig
    endpoint: str = "/api/v1/analysis-templates"
    field_mapping: Optional[Dict[str, str]] = None
    skip_duplicates: bool = True


class OneCTemplateImportResponse(BaseModel):
    """Ответ на импорт шаблонов из 1С."""
    status: str
    total: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: List[Dict[str, Any]] = []
    timestamp: str


# --- Планы ---

class OneCPlanImportRequest(BaseModel):
    """Запрос на импорт планов из 1С."""
    connection: OneCConnectionConfig
    endpoint: str = "/api/v1/analysis-plans"
    field_mapping: Optional[Dict[str, str]] = None
    skip_duplicates: bool = True


class OneCPlanImportResponse(BaseModel):
    """Ответ на импорт планов из 1С."""
    status: str
    total: int = 0
    created: int = 0
    skipped: int = 0
    errors: List[Dict[str, Any]] = []
    timestamp: str


# --- Проверка связи ---

class OneCTestConnectionRequest(BaseModel):
    """Запрос на проверку подключения к 1С."""
    connection: OneCConnectionConfig


class OneCTestConnectionResponse(BaseModel):
    """Ответ на проверку подключения к 1С."""
    status: str
    message: str
    timestamp: str


# ==================== Эндпоинты ====================

# --- Сохранение/загрузка конфигурации интеграции ---

@router.get("/1c/config", response_model=IntegrationConfigResponse)
async def get_1c_config(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Получить сохранённую конфигурацию 1С (без пароля)."""
    config = crud_integration.get_by_name(db, INTEGRATION_NAME)
    if config is None:
        return IntegrationConfigResponse(name=INTEGRATION_NAME)
    return IntegrationConfigResponse.model_validate(config)


@router.put("/1c/config", response_model=IntegrationConfigResponse)
async def save_1c_config(
    data: IntegrationConfigUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Сохранить конфигурацию 1С (URL, логин, пароль)."""
    config = crud_integration.upsert(db, INTEGRATION_NAME, data)
    return IntegrationConfigResponse.model_validate(config)


# --- Проверка связи ---

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
    from app.services.external_integration import (
        OneCIntegrationService,
        ExternalSystemConfig,
    )
    config = ExternalSystemConfig(
        base_url=request.connection.base_url,
        api_key=request.connection.api_key,
        username=request.connection.username,
        password=request.connection.password,
        timeout=request.connection.timeout,
        endpoint=request.connection.endpoint,
    )
    service = OneCIntegrationService(config)
    try:
        result = await service.test_connection()
        return OneCTestConnectionResponse(**result)
    finally:
        await service.close()


# ==================== Показатели ====================

@router.post("/1c/import-indicators")
async def import_indicators_from_1c(
    request: OneCImportRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Импортировать справочник показателей из 1С Предприятие.
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
        endpoint=request.connection.endpoint,
    )
    # Endpoint: из тела запроса, иначе из сохранённой конфигурации (indicators_endpoint)
    saved_config = crud_integration.get_by_name(db, INTEGRATION_NAME)
    endpoint = request.connection.endpoint or (
        saved_config.indicators_endpoint if saved_config else None
    ) or "/erp_24/hs/labindicators/indicators"
    try:
        result = await import_indicators_from_1c(
            db=db, config=config, endpoint=endpoint,
            field_mapping=request.field_mapping, skip_duplicates=request.skip_duplicates,
        )
        return OneCImportResponse(status="success" if not result["errors"] else "partial", **result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Import failed: {str(e)}")


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
    """
    from app.services.external_integration import OneCIntegrationService, ExternalSystemConfig
    config = ExternalSystemConfig(base_url=base_url, api_key=api_key, username=username, password=password)
    service = OneCIntegrationService(config)
    try:
        indicators = await service.fetch_indicators_from_1c(endpoint)
        return {"status": "success", "count": len(indicators), "indicators": indicators}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch: {str(e)}")
    finally:
        await service.close()


# ==================== Шаблоны анализов ====================

@router.post("/1c/import-templates")
async def import_templates_from_1c(
    request: OneCTemplateImportRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Импортировать шаблоны анализов из 1С Предприятие.
    
    Пример запроса:
    {
        "connection": {
            "base_url": "http://1c-server:8080",
            "api_key": "your-api-key"
        },
        "endpoint": "/api/v1/analysis-templates",
        "field_mapping": {
            "name": "Наименование",
            "description": "Описание",
            "is_active": "Активен",
            "indicators": "Показатели"
        },
        "skip_duplicates": true
    }
    
    Ожидаемый формат данных от 1С:
    [
        {
            "id": 1,
            "name": "Общий анализ крови",
            "description": "Шаблон для общего анализа",
            "is_active": true,
            "indicators": [
                {"indicator_id": 1, "min_value": 3.5, "max_value": 5.5, "sort_order": 0}
            ]
        }
    ]
    """
    from app.services.external_integration import (
        import_templates_from_1c,
        ExternalSystemConfig,
    )
    config = ExternalSystemConfig(
        base_url=request.connection.base_url,
        api_key=request.connection.api_key,
        username=request.connection.username,
        password=request.connection.password,
        timeout=request.connection.timeout,
    )
    # Endpoint: из тела запроса, иначе из сохранённой конфигурации (templates_endpoint)
    saved_config = crud_integration.get_by_name(db, INTEGRATION_NAME)
    endpoint = request.connection.endpoint or (
        saved_config.templates_endpoint if saved_config else None
    ) or "/erp_24/hs/labindicators/templates"
    try:
        result = await import_templates_from_1c(
            db=db, config=config, endpoint=endpoint,
            field_mapping=request.field_mapping, skip_duplicates=request.skip_duplicates,
        )
        return OneCTemplateImportResponse(status="success" if not result["errors"] else "partial", **result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Import failed: {str(e)}")


@router.get("/1c/templates")
async def fetch_templates_from_1c(
    base_url: str,
    api_key: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    endpoint: str = "/api/v1/analysis-templates",
    api_key_header: str = Depends(get_api_key),
):
    """
    Получить список шаблонов анализов из 1С без сохранения в БД.
    Полезно для предпросмотра данных перед импортом.
    """
    from app.services.external_integration import OneCIntegrationService, ExternalSystemConfig
    config = ExternalSystemConfig(base_url=base_url, api_key=api_key, username=username, password=password)
    service = OneCIntegrationService(config)
    try:
        templates = await service.fetch_templates_from_1c(endpoint)
        return {"status": "success", "count": len(templates), "templates": templates}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch: {str(e)}")
    finally:
        await service.close()


# ==================== Планы анализов ====================

@router.post("/1c/import-plans")
async def import_plans_from_1c(
    request: OneCPlanImportRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Импортировать планы анализов из 1С Предприятие.
    
    Пример запроса:
    {
        "connection": {
            "base_url": "http://1c-server:8080",
            "api_key": "your-api-key"
        },
        "endpoint": "/api/v1/analysis-plans",
        "field_mapping": {
            "name": "Наименование",
            "description": "Описание",
            "plan_date": "ДатаПлана",
            "items": "Элементы"
        },
        "skip_duplicates": true
    }
    
    Ожидаемый формат данных от 1С:
    [
        {
            "id": 1,
            "name": "План на 18.06.2026",
            "description": "План анализов на день",
            "plan_date": "2026-06-18",
            "items": [
                {"template_id": 1, "batch_number": "П-001", "sort_order": 0}
            ]
        }
    ]
    """
    from app.services.external_integration import (
        import_plans_from_1c,
        ExternalSystemConfig,
    )
    config = ExternalSystemConfig(
        base_url=request.connection.base_url,
        api_key=request.connection.api_key,
        username=request.connection.username,
        password=request.connection.password,
        timeout=request.connection.timeout,
    )
    # Endpoint: из тела запроса, иначе из сохранённой конфигурации (plans_endpoint)
    saved_config = crud_integration.get_by_name(db, INTEGRATION_NAME)
    endpoint = request.connection.endpoint or (
        saved_config.plans_endpoint if saved_config else None
    ) or "/erp_24/hs/labindicators/plans"
    try:
        result = await import_plans_from_1c(
            db=db, config=config, endpoint=endpoint,
            field_mapping=request.field_mapping, skip_duplicates=request.skip_duplicates,
        )
        return OneCPlanImportResponse(status="success" if not result["errors"] else "partial", **result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Import failed: {str(e)}")


@router.get("/1c/plans")
async def fetch_plans_from_1c(
    base_url: str,
    api_key: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    endpoint: str = "/api/v1/analysis-plans",
    api_key_header: str = Depends(get_api_key),
):
    """
    Получить список планов анализов из 1С без сохранения в БД.
    Полезно для предпросмотра данных перед импортом.
    """
    from app.services.external_integration import OneCIntegrationService, ExternalSystemConfig
    config = ExternalSystemConfig(base_url=base_url, api_key=api_key, username=username, password=password)
    service = OneCIntegrationService(config)
    try:
        plans = await service.fetch_plans_from_1c(endpoint)
        return {"status": "success", "count": len(plans), "plans": plans}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch: {str(e)}")
    finally:
        await service.close()


# ==================== Отправка данных в 1С ====================

@router.post("/1c/push-report")
async def push_report_to_1c(
    report_data: Dict[str, Any] = Body(...),
    base_url: str = Query(...),
    api_key: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    endpoint: str = "/api/v1/reports",
    api_key_header: str = Depends(get_api_key),
):
    """
    Отправить отчёт в 1С.
    
    Пример запроса:
    POST /api/external/1c/push-report?base_url=http://1c-server:8080
    {
        "report_id": 1,
        "batch_number": "П-001",
        "template_name": "Общий анализ",
        "values": [...]
    }
    """
    from app.services.external_integration import OneCIntegrationService, ExternalSystemConfig
    config = ExternalSystemConfig(base_url=base_url, api_key=api_key, username=username, password=password)
    service = OneCIntegrationService(config)
    try:
        result = await service.push_report_to_1c(report_data, endpoint)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Push failed: {str(e)}")
    finally:
        await service.close()


@router.post("/1c/push-plan")
async def push_plan_to_1c(
    plan_data: Dict[str, Any] = Body(...),
    base_url: str = Query(...),
    api_key: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    endpoint: str = "/api/v1/analysis-plans",
    api_key_header: str = Depends(get_api_key),
):
    """
    Отправить план в 1С.
    """
    from app.services.external_integration import OneCIntegrationService, ExternalSystemConfig
    config = ExternalSystemConfig(base_url=base_url, api_key=api_key, username=username, password=password)
    service = OneCIntegrationService(config)
    try:
        result = await service.push_plan_to_1c(plan_data, endpoint)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Push failed: {str(e)}")
    finally:
        await service.close()


# ==================== Устаревшие эндпоинты (совместимость) ====================

@router.post("/sync-templates")
def sync_templates(
    templates_data: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Синхронизация шаблонов из внешней ERP системы.
    Защита: статичный API-ключ в Header `X-API-KEY`.
    """
    try:
        for template_data in templates_data:
            existing_template = db.query(crud_template.AnalysisType).filter(
                crud_template.AnalysisType.name == template_data["name"]
            ).first()
            if existing_template:
                update_data = AnalysisTypeUpdate(
                    name=template_data.get("name", existing_template.name),
                    description=template_data.get("description")
                )
                crud_template.update_template(db, existing_template.id, update_data)
            else:
                create_data = AnalysisTypeCreate(
                    name=template_data["name"],
                    description=template_data.get("description")
                )
                crud_template.create_template(db, create_data, user_id=1)
        return {"message": f"Successfully synced {len(templates_data)} templates"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")