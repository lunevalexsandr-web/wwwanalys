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


def _build_service_config(connection, saved_config, default_endpoint: str = "/"):
    """Собрать конфиг подключения к 1С, подставляя сохранённые креды, если в
    запросе они пустые (форма не возвращает пароль по соображениям безопасности)."""
    from app.services.external_integration import ExternalSystemConfig
    return ExternalSystemConfig(
        base_url=(getattr(connection, "base_url", None) or (saved_config.base_url if saved_config else None) or ""),
        api_key=(getattr(connection, "api_key", None) or (saved_config.api_key if saved_config else None)),
        username=(getattr(connection, "username", None) or (saved_config.username if saved_config else None)),
        password=(getattr(connection, "password", None) or (saved_config.password if saved_config else None)),
        timeout=getattr(connection, "timeout", None) or 30,
        verify=bool(getattr(saved_config, "verify_ssl", False)) if saved_config else False,
        endpoint=(getattr(connection, "endpoint", None) or default_endpoint),
    )


# ==================== Схемы для интеграции с 1С ====================

class OneCConnectionConfig(BaseModel):
    """Конфигурация подключения к 1С."""
    base_url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    endpoint: str = "/erp_tek/hs/labindicators/indicators"


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
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Проверить подключение к 1С Предприятие. Пустые логин/пароль в запросе
    подставляются из сохранённой конфигурации.
    """
    from app.services.external_integration import OneCIntegrationService
    saved_config = crud_integration.get_by_name(db, INTEGRATION_NAME)
    default_ep = (saved_config.indicators_endpoint if saved_config else None) or "/erp_tek/odata/standard.odata/"
    config = _build_service_config(request.connection, saved_config, default_endpoint=default_ep)
    service = OneCIntegrationService(config)
    try:
        result = await service.test_connection()
        return OneCTestConnectionResponse(**result)
    finally:
        await service.close()


# ==================== Показатели (справочник) через OData ====================

class OneCODataIndicatorImportRequest(BaseModel):
    """Запрос на импорт справочника показателей из стандартного OData 1С."""
    connection: OneCConnectionConfig
    endpoint: Optional[str] = None  # напр. /erp_tek/odata/standard.odata/Catalog_Показатели
    name_field: str = "Description"
    unit_field: str = "ЕдиницаИзмерения"
    code_field: str = "Code"
    skip_duplicates: bool = False


@router.post("/1c/import-indicators-odata")
async def import_indicators_from_1c_odata(
    request: OneCODataIndicatorImportRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Импортировать справочник показателей из СТАНДАРТНОГО OData 1С.

    Сопоставление по Ref_Key (external_id). Именно external_id используется затем
    при импорте шаблонов для связи показателей. Подключение берётся из вкладки
    «Интеграция с 1С».
    """
    from app.services.external_integration import (
        import_odata_indicators_from_1c,
        ExternalSystemConfig,
    )
    saved_config = crud_integration.get_by_name(db, INTEGRATION_NAME)
    config = _build_service_config(request.connection, saved_config)
    endpoint = request.endpoint or (
        saved_config.indicators_endpoint if saved_config else None
    )
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не задан endpoint OData для показателей (вкладка «Интеграция с 1С»)",
        )
    try:
        result = await import_odata_indicators_from_1c(
            db=db, config=config, endpoint=endpoint,
            skip_duplicates=request.skip_duplicates,
            name_field=request.name_field,
            unit_field=request.unit_field,
            code_field=request.code_field,
        )
        return {"status": "success" if not result["errors"] else "partial", **result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"OData import failed: {str(e)}")


# --- Варианты значений показателей (ДопАналитика) через OData ---

class OneCODataOptionsImportRequest(BaseModel):
    """Запрос на импорт вариантов значений показателей (список для select)."""
    connection: OneCConnectionConfig
    endpoint: Optional[str] = None  # напр. /erp_tek/odata/standard.odata/Catalog__ДопАналитикаПоказателейАнализов
    owner_field: str = "Owner_Key"
    value_field: str = "Description"


@router.post("/1c/import-indicator-options-odata")
async def import_indicator_options_from_1c_odata(
    request: OneCODataOptionsImportRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Импортировать варианты значений показателей из OData 1С
    (подчинённый справочник ДопАналитикаПоказателейАнализов).

    Для показателей с вариантами проставляется options (список) и data_type='select'.
    Сопоставление по external_id показателя (== Owner_Key варианта).
    """
    from app.services.external_integration import (
        import_odata_indicator_options_from_1c,
    )
    saved_config = crud_integration.get_by_name(db, INTEGRATION_NAME)
    config = _build_service_config(request.connection, saved_config)
    endpoint = request.endpoint or (
        getattr(saved_config, "options_endpoint", None) if saved_config else None
    )
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не задан endpoint OData для вариантов значений (вкладка «Интеграция с 1С»)",
        )
    try:
        result = await import_odata_indicator_options_from_1c(
            db=db, config=config, endpoint=endpoint,
            owner_field=request.owner_field, value_field=request.value_field,
        )
        return {"status": "success" if not result["errors"] else "partial", **result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"OData import failed: {str(e)}")


# --- Ёмкости/танки из справочника Склады ---

class OneCODataStorageImportRequest(BaseModel):
    """Запрос на загрузку ёмкостей/танков из справочника Склады (папка Емкости)."""
    connection: OneCConnectionConfig
    endpoint: Optional[str] = None  # напр. /erp_tek/odata/standard.odata/Catalog_Склады


@router.post("/1c/import-storage-options-odata")
async def import_storage_options_from_1c_odata(
    request: OneCODataStorageImportRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Наполнить показатели «Номер ёмкости»/«Номер танка» вариантами из справочника
    Склады (папка «Емкости» и подпапка «Танки»)."""
    from app.services.external_integration import import_odata_storage_options_from_1c
    saved_config = crud_integration.get_by_name(db, INTEGRATION_NAME)
    config = _build_service_config(request.connection, saved_config)
    endpoint = request.endpoint or (
        getattr(saved_config, "storage_endpoint", None) if saved_config else None
    )
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не задан endpoint OData для справочника Склады (вкладка «Интеграция с 1С»)",
        )
    try:
        result = await import_odata_storage_options_from_1c(db=db, config=config, endpoint=endpoint)
        return {"status": "success" if not result["errors"] else "partial", **result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"OData import failed: {str(e)}")


# --- Шаблоны через стандартный OData 1С ---

class OneCODataTemplateImportRequest(BaseModel):
    """Запрос на импорт шаблонов из стандартного OData 1С (ТиповыеАнализыСерий)."""
    connection: OneCConnectionConfig
    endpoint: Optional[str] = None  # напр. /erp_tek/odata/standard.odata/Catalog__ТиповыеАнализыСерий
    indicators_field: str = "ПоказателиАнализа"
    norms_field: str = "Нормативы"
    indicator_key_field: str = "Показатель_Key"
    name_field: str = "Description"
    skip_duplicates: bool = True
    create_missing_indicators: bool = False


@router.post("/1c/import-templates-odata")
async def import_templates_from_1c_odata(
    request: OneCODataTemplateImportRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Импортировать шаблоны анализов из СТАНДАРТНОГО OData 1С
    (справочник ТиповыеАнализыСерий с табличными частями ПоказателиАнализа/Нормативы).

    Показатели сопоставляются со справочником по GUID (external_id). Перед импортом
    шаблонов рекомендуется импортировать справочник показателей.

    Пример тела:
    {
        "connection": {
            "base_url": "https://mp.rugen.ru:8443",
            "username": "odata_user",
            "password": "***"
        },
        "endpoint": "/erp_tek/odata/standard.odata/Catalog__ТиповыеАнализыСерий",
        "skip_duplicates": true
    }
    """
    from app.services.external_integration import (
        import_odata_templates_from_1c,
        ExternalSystemConfig,
    )
    saved_config = crud_integration.get_by_name(db, INTEGRATION_NAME)
    config = _build_service_config(request.connection, saved_config)
    endpoint = request.endpoint or (
        saved_config.templates_endpoint if saved_config else None
    ) or "/erp_tek/odata/standard.odata/Catalog__ТиповыеАнализыСерий"
    try:
        result = await import_odata_templates_from_1c(
            db=db,
            config=config,
            endpoint=endpoint,
            skip_duplicates=request.skip_duplicates,
            indicators_field=request.indicators_field,
            norms_field=request.norms_field,
            indicator_key_field=request.indicator_key_field,
            name_field=request.name_field,
            create_missing_indicators=request.create_missing_indicators,
            variants_endpoint=(getattr(saved_config, "options_endpoint", None) if saved_config else None),
        )
        return {"status": "success" if not result["errors"] else "partial", **result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OData import failed: {str(e)}"
        )


# ==================== Сорта (справочник) ====================

class OneCODataVarietyImportRequest(BaseModel):
    """Запрос на импорт справочника сортов из стандартного OData 1С."""
    connection: OneCConnectionConfig
    endpoint: Optional[str] = None  # напр. /erp_tek/odata/standard.odata/Catalog_Сорта
    name_field: str = "Description"
    code_field: str = "Code"
    skip_duplicates: bool = False


@router.post("/1c/import-varieties-odata")
async def import_varieties_from_1c_odata(
    request: OneCODataVarietyImportRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Импортировать справочник сортов из СТАНДАРТНОГО OData 1С.

    Сопоставление по Ref_Key (external_id), фолбэк по имени. Подключение
    (base_url/логин/пароль) берётся из вкладки «Интеграция с 1С».
    """
    from app.services.external_integration import (
        import_odata_varieties_from_1c,
        ExternalSystemConfig,
    )
    saved_config = crud_integration.get_by_name(db, INTEGRATION_NAME)
    config = _build_service_config(request.connection, saved_config)
    endpoint = request.endpoint or (
        getattr(saved_config, "varieties_endpoint", None) if saved_config else None
    )
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не задан endpoint OData для сортов (вкладка «Интеграция с 1С»)",
        )
    try:
        result = await import_odata_varieties_from_1c(
            db=db,
            config=config,
            endpoint=endpoint,
            skip_duplicates=request.skip_duplicates,
            name_field=request.name_field,
            code_field=request.code_field,
        )
        return {"status": "success" if not result["errors"] else "partial", **result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OData import failed: {str(e)}"
        )


# ==================== Планы анализов через OData ====================

class OneCODataPlanImportRequest(BaseModel):
    """Запрос на импорт планов анализов из стандартного OData 1С (документ)."""
    connection: OneCConnectionConfig
    endpoint: Optional[str] = None  # напр. /erp_tek/odata/standard.odata/Document_ПланАнализов
    name_field: str = "Number"
    date_field: str = "Date"
    items_field: str = "СоставАнализов"
    template_key_field: str = "ТиповойАнализ_Key"
    batch_field: str = "Серия"
    skip_duplicates: bool = True


@router.post("/1c/import-plans-odata")
async def import_plans_from_1c_odata(
    request: OneCODataPlanImportRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Импортировать планы анализов из СТАНДАРТНОГО OData 1С (документ с табличной частью).

    Шаблоны позиций сопоставляются со справочником по external_id (GUID) — сначала
    импортируйте шаблоны. Имена полей документа настраиваются в теле запроса.
    """
    from app.services.external_integration import (
        import_odata_plans_from_1c,
        ExternalSystemConfig,
    )
    saved_config = crud_integration.get_by_name(db, INTEGRATION_NAME)
    config = _build_service_config(request.connection, saved_config)
    endpoint = request.endpoint or (
        saved_config.plans_endpoint if saved_config else None
    )
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не задан endpoint OData для планов (вкладка «Интеграция с 1С»)",
        )
    try:
        result = await import_odata_plans_from_1c(
            db=db, config=config, endpoint=endpoint,
            skip_duplicates=request.skip_duplicates,
            name_field=request.name_field,
            date_field=request.date_field,
            items_field=request.items_field,
            template_key_field=request.template_key_field,
            batch_field=request.batch_field,
        )
        return {"status": "success" if not result["errors"] else "partial", **result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"OData import failed: {str(e)}")


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