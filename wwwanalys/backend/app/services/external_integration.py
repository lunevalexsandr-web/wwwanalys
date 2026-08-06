"""
Сервис для интеграции с внешними системами (1С Предприятие и др.)
Поддерживает:
- Импорт справочника показателей из внешних источников
- Синхронизацию шаблонов анализов с 1С
- Синхронизацию планов анализов с 1С
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date

import httpx
from sqlalchemy.orm import Session

from app.models import IndicatorLibrary, AnalysisType, TemplateIndicator, AnalysisPlan, PlanItem
from app.schemas.indicator_library import (
    IndicatorLibraryCreate,
    BatchCreateItem,
    BatchCreateResponse,
)

logger = logging.getLogger(__name__)


class ExternalSystemConfig:
    """Конфигурация для подключения к внешней системе."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
        verify: bool = False,
        endpoint: str = "/erp_tek/hs/labindicators/indicators",
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.username = username
        self.password = password
        self.timeout = timeout
        # 1С часто использует самоподписанные сертификаты — отключаем проверку по умолчанию
        self.verify = verify
        # Путь к HTTP-сервису 1С (endpoint показателей)
        self.endpoint = endpoint


class OneCIntegrationService:
    """
    Сервис для интеграции с 1С Предприятие.
    
    Поддерживает:
    - Загрузку справочника показателей из 1С
    - Синхронизацию шаблонов анализов
    - Синхронизацию планов анализов
    - Обработку ошибок и логирование
    """

    def __init__(self, config: ExternalSystemConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Получить или создать HTTP-клиент."""
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.config.api_key:
                headers["X-API-KEY"] = self.config.api_key
            elif self.config.username and self.config.password:
                import base64
                credentials = base64.b64encode(
                    f"{self.config.username}:{self.config.password}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {credentials}"

            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=headers,
                timeout=self.config.timeout,
                verify=self.config.verify,
            )
        return self._client

    async def close(self):
        """Закрыть HTTP-клиент."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _fetch_list(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Универсальный метод для загрузки списка из 1С."""
        client = await self._get_client()
        response = await client.get(endpoint, params=params or {})
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if key and key in data:
                return data[key]
            for k in ("items", "data", "results", "value"):
                if k in data:
                    return data[k]
            return [data]
        else:
            raise ValueError(f"Unexpected response format: {type(data)}")

    # ==================== Показатели ====================

    async def fetch_indicators_from_1c(
        self,
        endpoint: str = "/api/v1/indicators",
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Загрузить список показателей из 1С.
        """
        return await self._fetch_list(endpoint, params)

    async def fetch_indicator_by_id_from_1c(
        self,
        indicator_id: str,
        endpoint_prefix: str = "/api/v1/indicators",
    ) -> Optional[Dict[str, Any]]:
        """Загрузить один показатель из 1С по ID."""
        client = await self._get_client()
        try:
            response = await client.get(f"{endpoint_prefix}/{indicator_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error fetching indicator {indicator_id} from 1C: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error fetching indicator {indicator_id} from 1C: {str(e)}")
            raise

    # ==================== Шаблоны анализов ====================

    async def fetch_templates_from_1c(
        self,
        endpoint: str = "/api/v1/analysis-templates",
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Загрузить список шаблонов анализов из 1С.
        
        Ожидаемый формат ответа 1С:
        [
            {
                "id": 1,
                "name": "Общий анализ крови",
                "description": "Шаблон для общего анализа",
                "is_active": true,
                "indicators": [
                    {"indicator_id": 1, "min_value": 3.5, "max_value": 5.5, "sort_order": 0},
                    ...
                ]
            }
        ]
        """
        return await self._fetch_list(endpoint, params)

    async def fetch_template_by_id_from_1c(
        self,
        template_id: str,
        endpoint_prefix: str = "/api/v1/analysis-templates",
    ) -> Optional[Dict[str, Any]]:
        """Загрузить один шаблон из 1С по ID."""
        client = await self._get_client()
        try:
            response = await client.get(f"{endpoint_prefix}/{template_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error fetching template {template_id} from 1C: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error fetching template {template_id} from 1C: {str(e)}")
            raise

    # ==================== Планы анализов ====================

    async def fetch_plans_from_1c(
        self,
        endpoint: str = "/api/v1/analysis-plans",
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Загрузить список планов анализов из 1С.
        
        Ожидаемый формат ответа 1С:
        [
            {
                "id": 1,
                "name": "План на 18.06.2026",
                "description": "План анализов на день",
                "plan_date": "2026-06-18",
                "items": [
                    {
                        "template_id": 1,
                        "batch_number": "П-001",
                        "sort_order": 0
                    },
                    ...
                ]
            }
        ]
        """
        return await self._fetch_list(endpoint, params)

    async def fetch_plan_by_id_from_1c(
        self,
        plan_id: str,
        endpoint_prefix: str = "/api/v1/analysis-plans",
    ) -> Optional[Dict[str, Any]]:
        """Загрузить один план из 1С по ID."""
        client = await self._get_client()
        try:
            response = await client.get(f"{endpoint_prefix}/{plan_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error fetching plan {plan_id} from 1C: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error fetching plan {plan_id} from 1C: {str(e)}")
            raise

    # ==================== Отправка данных в 1С ====================

    async def push_report_to_1c(
        self,
        report_data: Dict[str, Any],
        endpoint: str = "/api/v1/reports",
    ) -> Dict[str, Any]:
        """
        Отправить отчёт в 1С.
        
        Args:
            report_data: Данные отчёта для отправки
            endpoint: API-эндпоинт в 1С
            
        Returns:
            Ответ от 1С
        """
        client = await self._get_client()
        try:
            response = await client.post(endpoint, json=report_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error pushing report to 1C: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error pushing report to 1C: {str(e)}")
            raise

    async def push_plan_to_1c(
        self,
        plan_data: Dict[str, Any],
        endpoint: str = "/api/v1/analysis-plans",
    ) -> Dict[str, Any]:
        """
        Отправить план в 1С.
        
        Args:
            plan_data: Данные плана для отправки
            endpoint: API-эндпоинт в 1С
            
        Returns:
            Ответ от 1С
        """
        client = await self._get_client()
        try:
            response = await client.post(endpoint, json=plan_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error pushing plan to 1C: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error pushing plan to 1C: {str(e)}")
            raise

    # ==================== Проверка связи ====================

    async def test_connection(self) -> Dict[str, Any]:
        """
        Проверить подключение к 1С.
        Использует реальный endpoint показателей (self.config.endpoint).
        """
        client = await self._get_client()
        try:
            response = await client.get(self.config.endpoint, timeout=10)
            if response.status_code == 200:
                return {
                    "status": "ok",
                    "message": "Connection to 1C successful",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                return {
                    "status": "warning",
                    "message": f"1C responded with status {response.status_code}",
                    "timestamp": datetime.utcnow().isoformat(),
                }
        except httpx.ConnectError:
            return {
                "status": "error",
                "message": f"Cannot connect to 1C at {self.config.base_url}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# ==================== Трансформация данных ====================

def transform_1c_indicator_to_local(
    indicator_1c: Dict[str, Any],
    field_mapping: Optional[Dict[str, str]] = None,
) -> Optional[BatchCreateItem]:
    """
    Преобразовать показатель из формата 1С в локальный формат.
    """
    default_mapping = {
        "name": "name",
        "unit": "unit",
        "data_type": "data_type",
        "description": "description",
        "category": "category",
        "is_required": "is_required",
        "default_value": "default_value",
        "options": "options",
    }
    mapping = field_mapping or default_mapping
    try:
        name = indicator_1c.get(mapping.get("name", "name"))
        if not name:
            logger.warning(f"Indicator without name: {indicator_1c}")
            return None
        result = {
            "name": name,
            "external_id": str(indicator_1c.get("id", "")) or None,
        }
        if "unit" in mapping:
            result["unit"] = indicator_1c.get(mapping["unit"])
        if "data_type" in mapping:
            data_type_1c = indicator_1c.get(mapping["data_type"], "number")
            data_type_mapping = {
                "number": "number", "numeric": "number", "integer": "number",
                "string": "text", "text": "text",
                "boolean": "number", "select": "select", "enum": "select",
            }
            result["data_type"] = data_type_mapping.get(str(data_type_1c).lower(), "number")
        if "description" in mapping:
            result["description"] = indicator_1c.get(mapping["description"])
        if "category" in mapping:
            result["category"] = indicator_1c.get(mapping["category"])
        if "is_required" in mapping:
            result["is_required"] = bool(indicator_1c.get(mapping["is_required"], False))
        if "default_value" in mapping:
            default_val = indicator_1c.get(mapping["default_value"])
            if default_val is not None:
                result["default_value"] = str(default_val)
        if "options" in mapping:
            options = indicator_1c.get(mapping["options"])
            if options:
                if isinstance(options, str):
                    result["options"] = [x.strip() for x in options.split(",") if x.strip()]
                elif isinstance(options, list):
                    result["options"] = [str(x) for x in options]
        return BatchCreateItem(**result)
    except Exception as e:
        logger.error(f"Error transforming indicator: {e}, data: {indicator_1c}")
        return None


def transform_1c_template_to_local(
    template_1c: Dict[str, Any],
    field_mapping: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Преобразовать шаблон из формата 1С в локальный формат.
    
    Ожидаемый формат 1С:
    {
        "id": 1,
        "name": "Общий анализ",
        "description": "Описание",
        "is_active": true,
        "indicators": [
            {"indicator_id": 1, "min_value": 3.5, "max_value": 5.5, "sort_order": 0}
        ]
    }
    """
    name_field = (field_mapping or {}).get("name", "name")
    desc_field = (field_mapping or {}).get("description", "description")
    active_field = (field_mapping or {}).get("is_active", "is_active")
    indicators_field = (field_mapping or {}).get("indicators", "indicators")

    try:
        name = template_1c.get(name_field)
        if not name:
            logger.warning(f"Template without name: {template_1c}")
            return None

        result = {
            "name": name,
            "description": template_1c.get(desc_field),
            "is_active": bool(template_1c.get(active_field, True)),
            "external_id": str(template_1c.get("id", "")) or None,
            "library_indicators": [],
        }

        indicators_1c = template_1c.get(indicators_field, [])
        if isinstance(indicators_1c, list):
            for idx, ind_ref in enumerate(indicators_1c):
                indicator_1c_id = ind_ref.get("indicator_id", ind_ref.get("id"))
                lib_ref = {
                    "indicator_id": indicator_1c_id,
                    "indicator_external_id": str(indicator_1c_id) if indicator_1c_id is not None else None,
                    "min_value": ind_ref.get("min_value"),
                    "max_value": ind_ref.get("max_value"),
                    "sort_order": ind_ref.get("sort_order", idx),
                    "external_id": str(ind_ref.get("id", "")) or None,
                    "name": ind_ref.get("name"),
                    "unit": ind_ref.get("unit"),
                    "data_type": ind_ref.get("data_type"),
                    "description": ind_ref.get("description"),
                }
                if lib_ref["indicator_id"]:
                    result["library_indicators"].append(lib_ref)

        return result
    except Exception as e:
        logger.error(f"Error transforming template: {e}, data: {template_1c}")
        return None


def transform_1c_plan_to_local(
    plan_1c: Dict[str, Any],
    field_mapping: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Преобразовать план из формата 1С в локальный формат.
    
    Ожидаемый формат 1С:
    {
        "id": 1,
        "name": "План на 18.06",
        "description": "Описание",
        "plan_date": "2026-06-18",
        "items": [
            {"template_id": 1, "batch_number": "П-001", "sort_order": 0}
        ]
    }
    """
    name_field = (field_mapping or {}).get("name", "name")
    desc_field = (field_mapping or {}).get("description", "description")
    date_field = (field_mapping or {}).get("plan_date", "plan_date")
    items_field = (field_mapping or {}).get("items", "items")

    try:
        name = plan_1c.get(name_field)
        if not name:
            logger.warning(f"Plan without name: {plan_1c}")
            return None

        plan_date_raw = plan_1c.get(date_field)
        if isinstance(plan_date_raw, str):
            plan_date = date.fromisoformat(plan_date_raw)
        elif isinstance(plan_date_raw, date):
            plan_date = plan_date_raw
        else:
            plan_date = date.today()

        result = {
            "name": name,
            "description": plan_1c.get(desc_field),
            "plan_date": plan_date,
            "plan_items": [],
        }

        items_1c = plan_1c.get(items_field, [])
        if isinstance(items_1c, list):
            for idx, item in enumerate(items_1c):
                plan_item = {
                    "template_id": item.get("template_id", item.get("analysis_type_id")),
                    "batch_number": item.get("batch_number", ""),
                    "sort_order": item.get("sort_order", idx),
                }
                if plan_item["template_id"]:
                    result["plan_items"].append(plan_item)

        return result
    except Exception as e:
        logger.error(f"Error transforming plan: {e}, data: {plan_1c}")
        return None


# ==================== Функции импорта ====================

async def import_indicators_from_1c(
    db: Session,
    config: ExternalSystemConfig,
    endpoint: str = "/api/v1/indicators",
    field_mapping: Optional[Dict[str, str]] = None,
    skip_duplicates: bool = True,
) -> Dict[str, Any]:
    """
    Импортировать показатели из 1С в локальную БД.
    """
    service = OneCIntegrationService(config)
    result = {
        "total": 0, "created": 0, "updated": 0, "skipped": 0,
        "errors": [], "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        indicators_1c = await service.fetch_indicators_from_1c(endpoint)
        result["total"] = len(indicators_1c)
        logger.info(f"Fetched {len(indicators_1c)} indicators from 1C")

        # Загружаем существующие показатели для быстрого поиска дублей
        existing_by_external_id: Dict[str, IndicatorLibrary] = {}
        existing_names: set = set()
        if skip_duplicates:
            for ind in db.query(IndicatorLibrary).all():
                if ind.external_id:
                    existing_by_external_id[str(ind.external_id)] = ind
                existing_names.add(ind.name)

        for indicator_data in indicators_1c:
            try:
                local_item = transform_1c_indicator_to_local(indicator_data, field_mapping)
                if local_item is None:
                    result["errors"].append({"indicator": indicator_data, "error": "Failed to transform"})
                    continue

                ext_id = local_item.external_id
                # Проверяем дубликат по external_id (ID из 1С)
                if ext_id and ext_id in existing_by_external_id:
                    if skip_duplicates:
                        result["skipped"] += 1
                        continue
                    # Обновляем существующий (по external_id)
                    existing = existing_by_external_id[ext_id]
                    existing.name = local_item.name
                    existing.unit = local_item.unit
                    existing.data_type = local_item.data_type
                    existing.options = ",".join(local_item.options) if local_item.options else None
                    existing.description = local_item.description
                    existing.category = local_item.category
                    existing.is_required = local_item.is_required
                    existing.default_value = local_item.default_value
                    result["updated"] += 1
                    continue

                # Проверяем дубликат по имени
                if skip_duplicates and local_item.name in existing_names:
                    # Если у существующего нет external_id — проставим его
                    existing_by_name = db.query(IndicatorLibrary).filter(
                        IndicatorLibrary.name == local_item.name
                    ).first()
                    if existing_by_name and ext_id and not existing_by_name.external_id:
                        existing_by_name.external_id = ext_id
                        db.flush()
                        existing_by_external_id[ext_id] = existing_by_name
                    result["skipped"] += 1
                    continue

                db_indicator = IndicatorLibrary(
                    name=local_item.name, unit=local_item.unit,
                    data_type=local_item.data_type,
                    options=",".join(local_item.options) if local_item.options else None,
                    description=local_item.description, category=local_item.category,
                    is_required=local_item.is_required, default_value=local_item.default_value,
                    external_id=ext_id,
                )
                db.add(db_indicator)
                result["created"] += 1
                existing_names.add(local_item.name)
                if ext_id:
                    existing_by_external_id[ext_id] = db_indicator
            except Exception as e:
                logger.error(f"Error processing indicator: {e}")
                result["errors"].append({"indicator": indicator_data, "error": str(e)})

        db.commit()
        logger.info(f"Import completed: {result['created']} created, {result['updated']} updated, {result['skipped']} skipped, {len(result['errors'])} errors")
    except Exception as e:
        db.rollback()
        logger.error(f"Import failed: {str(e)}")
        result["errors"].append({"error": str(e)})
        raise
    finally:
        await service.close()
    return result


async def import_templates_from_1c(
    db: Session,
    config: ExternalSystemConfig,
    endpoint: str = "/api/v1/analysis-templates",
    field_mapping: Optional[Dict[str, str]] = None,
    skip_duplicates: bool = True,
    user_id: int = 1,
) -> Dict[str, Any]:
    """
    Импортировать шаблоны анализов из 1С в локальную БД.
    Шаблон загружается "наполненным" — показатели привязываются по external_id из 1С.
    
    Returns:
        {
            "total": 10,
            "created": 5,
            "skipped": 3,
            "updated": 2,
            "errors": []
        }
    """
    service = OneCIntegrationService(config)
    result = {
        "total": 0, "created": 0, "skipped": 0, "updated": 0,
        "errors": [], "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        templates_1c = await service.fetch_templates_from_1c(endpoint)
        result["total"] = len(templates_1c)
        logger.info(f"Fetched {len(templates_1c)} templates from 1C")

        for template_data in templates_1c:
            try:
                local_data = transform_1c_template_to_local(template_data, field_mapping)
                if local_data is None:
                    result["errors"].append({"template": template_data, "error": "Failed to transform"})
                    continue

                template_external_id = local_data.get("external_id")

                # Ищем шаблон по external_id (из 1С) или по имени
                existing = None
                if template_external_id:
                    existing = db.query(AnalysisType).filter(
                        AnalysisType.external_id == template_external_id
                    ).first()
                if existing is None:
                    existing = db.query(AnalysisType).filter(
                        AnalysisType.name == local_data["name"]
                    ).first()

                if existing:
                    if skip_duplicates:
                        result["skipped"] += 1
                        continue
                    # Обновляем существующий
                    existing.description = local_data.get("description") or existing.description
                    existing.is_active = local_data.get("is_active", existing.is_active)
                    existing.external_id = template_external_id
                    # Обновляем показатели
                    for ti in existing.template_indicators:
                        db.delete(ti)
                    db.flush()
                    for lib_ref in local_data.get("library_indicators", []):
                        indicator = _resolve_indicator_by_external_id(db, lib_ref, user_id)
                        if indicator is None:
                            result["errors"].append({
                                "template": local_data["name"],
                                "error": f"Не удалось найти/создать показатель с external_id={lib_ref.get('external_id')}"
                            })
                            continue
                        ti = TemplateIndicator(
                            template_id=existing.id,
                            indicator_id=indicator.id,
                            min_value=lib_ref.get("min_value"),
                            max_value=lib_ref.get("max_value"),
                            sort_order=lib_ref.get("sort_order", 0),
                            external_id=lib_ref.get("external_id"),
                        )
                        db.add(ti)
                    result["updated"] += 1
                else:
                    # Создаём новый шаблон
                    db_template = AnalysisType(
                        name=local_data["name"],
                        description=local_data.get("description"),
                        created_by=user_id,
                        is_active=local_data.get("is_active", True),
                        external_id=template_external_id,
                    )
                    db.add(db_template)
                    db.flush()
                    for lib_ref in local_data.get("library_indicators", []):
                        indicator = _resolve_indicator_by_external_id(db, lib_ref, user_id)
                        if indicator is None:
                            result["errors"].append({
                                "template": local_data["name"],
                                "error": f"Не удалось найти/создать показатель с external_id={lib_ref.get('external_id')}"
                            })
                            continue
                        ti = TemplateIndicator(
                            template_id=db_template.id,
                            indicator_id=indicator.id,
                            min_value=lib_ref.get("min_value"),
                            max_value=lib_ref.get("max_value"),
                            sort_order=lib_ref.get("sort_order", 0),
                            external_id=lib_ref.get("external_id"),
                        )
                        db.add(ti)
                    result["created"] += 1

            except Exception as e:
                logger.error(f"Error processing template: {e}")
                result["errors"].append({"template": template_data, "error": str(e)})

        db.commit()
        logger.info(
            f"Templates import: {result['created']} created, {result['updated']} updated, "
            f"{result['skipped']} skipped, {len(result['errors'])} errors"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Templates import failed: {str(e)}")
        result["errors"].append({"error": str(e)})
        raise
    finally:
        await service.close()
    return result


def _resolve_indicator_by_external_id(db: Session, lib_ref: Dict[str, Any], user_id: int) -> Optional[IndicatorLibrary]:
    """
    Найти показатель по external_id (ID показателя из 1С).
    При импорте шаблона из 1С в lib_ref приходит:
      - indicator_external_id: это ID показателя в 1С (используется для сопоставления)
      - external_id: это ID связи показателя в шаблоне (сохраняется в TemplateIndicator)
    Если показатель не найден — создаём новый с external_id = indicator_external_id.
    Возвращает IndicatorLibrary или None.
    """
    # ID показателя из 1С (для сопоставления со справочником)
    indicator_external_id = lib_ref.get("indicator_external_id") or lib_ref.get("external_id")
    # Имя показателя (если 1С передаёт его в связи)
    name = lib_ref.get("name")
    if not name:
        if indicator_external_id:
            name = f"Показатель {indicator_external_id}"
        else:
            name = f"Показатель {lib_ref.get('indicator_id')}"

    # Сначала ищем по external_id показателя
    if indicator_external_id:
        indicator = db.query(IndicatorLibrary).filter(
            IndicatorLibrary.external_id == str(indicator_external_id)
        ).first()
        if indicator:
            return indicator

    # Если не найден по external_id — ищем по имени
    existing_by_name = db.query(IndicatorLibrary).filter(IndicatorLibrary.name == name).first()
    if existing_by_name:
        # Если у существующего нет external_id — проставим его
        if indicator_external_id and not existing_by_name.external_id:
            existing_by_name.external_id = str(indicator_external_id)
            db.flush()
        return existing_by_name

    # Создаём новый показатель
    indicator = IndicatorLibrary(
        name=name,
        unit=lib_ref.get("unit"),
        data_type=lib_ref.get("data_type", "number"),
        description=lib_ref.get("description"),
        external_id=str(indicator_external_id) if indicator_external_id else None,
        created_by=user_id,
    )
    db.add(indicator)
    db.flush()
    return indicator


# ==================== OData 1С: шаблоны (Catalog__ТиповыеАнализыСерий) ====================

ZERO_GUID = "00000000-0000-0000-0000-000000000000"


def _odata_num(value: Any) -> Optional[float]:
    """Число из OData 1С в float или None (пусто/Undefined -> None)."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _etalon_ref_text(val: Any, vtype: Any, variant_map: Optional[Dict[str, str]]) -> Optional[str]:
    """Текст нечисловой границы нормы (ЭталонОт/ЭталонДо).

    Если это ссылка на справочник вариантов (ДопАналитика) — резолвим GUID в текст
    по variant_map; если строка — берём как есть; числа и пустое игнорируем.
    """
    if val in (None, "") or str(val) == ZERO_GUID:
        return None
    t = str(vtype or "")
    if "ДопАналитика" in t:
        return (variant_map or {}).get(str(val).lower())
    if t == "Edm.String":
        return str(val).strip() or None
    return None


def transform_1c_odata_template_to_local(
    template_1c: Dict[str, Any],
    indicators_field: str = "ПоказателиАнализа",
    norms_field: str = "Нормативы",
    indicator_key_field: str = "Показатель_Key",
    name_field: str = "Description",
    variant_map: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Преобразовать шаблон из стандартного OData 1С (справочник ТиповыеАнализыСерий)
    в локальный формат.

    - name          <- Description
    - external_id   <- Ref_Key (GUID шаблона)
    - показатели    <- табличная часть `ПоказателиАнализа` (ссылка Показатель_Key = GUID)
    - мин/макс      <- ЭталонОт/ЭталонДо (числовые); фолбэк на ТЧ `Нормативы` Минимум/Максимум
    - norm_text     <- нечисловая норма ЭталонОт/ЭталонДо (ссылки на варианты → текст)
    Группы (IsFolder) и помеченные на удаление (DeletionMark) должны отсекаться ДО вызова.
    """
    name = template_1c.get(name_field)
    if not name:
        return None

    ref_key = template_1c.get("Ref_Key")

    # Числовые нормы из ТЧ Нормативы: Показатель_Key -> (min, max)
    norms_map: Dict[str, tuple] = {}
    for norm in (template_1c.get(norms_field) or []):
        key = norm.get(indicator_key_field)
        if key and key != ZERO_GUID:
            norms_map[str(key)] = (
                _odata_num(norm.get("Минимум")),
                _odata_num(norm.get("Максимум")),
            )

    library_indicators: List[Dict[str, Any]] = []
    seen: set = set()
    for row in (template_1c.get(indicators_field) or []):
        key = row.get(indicator_key_field)
        if not key or key == ZERO_GUID or str(key) in seen:
            continue
        seen.add(str(key))
        # Числовая норма: сначала ЭталонОт/ЭталонДо, фолбэк на ТЧ Нормативы
        nmin = _odata_num(row.get("ЭталонОт"))
        nmax = _odata_num(row.get("ЭталонДо"))
        if nmin is None or nmax is None:
            fb_min, fb_max = norms_map.get(str(key), (None, None))
            nmin = nmin if nmin is not None else fb_min
            nmax = nmax if nmax is not None else fb_max
        # Нечисловая норма: ЭталонОт/ЭталонДо как ссылки на варианты (или строки)
        ot_t = _etalon_ref_text(row.get("ЭталонОт"), row.get("ЭталонОт_Type"), variant_map)
        do_t = _etalon_ref_text(row.get("ЭталонДо"), row.get("ЭталонДо_Type"), variant_map)
        if ot_t and do_t:
            norm_text = ot_t if ot_t == do_t else f"{ot_t} – {do_t}"
        else:
            norm_text = ot_t or do_t
        library_indicators.append({
            "indicator_external_id": str(key),
            "external_id": str(key),
            "min_value": nmin,
            "max_value": nmax,
            "norm_text": norm_text,
            "sort_order": row.get("LineNumber") or (len(library_indicators) + 1),
        })

    return {
        "name": name,
        "description": template_1c.get("НаименованиеENG") or None,
        "is_active": not bool(template_1c.get("DeletionMark", False)),
        "external_id": str(ref_key) if ref_key else None,
        "library_indicators": library_indicators,
    }


async def import_odata_templates_from_1c(
    db: Session,
    config: ExternalSystemConfig,
    endpoint: str = "/erp_tek/odata/standard.odata/Catalog__ТиповыеАнализыСерий",
    skip_duplicates: bool = True,
    user_id: int = 1,
    indicators_field: str = "ПоказателиАнализа",
    norms_field: str = "Нормативы",
    indicator_key_field: str = "Показатель_Key",
    name_field: str = "Description",
    create_missing_indicators: bool = False,
    variants_endpoint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Импортировать шаблоны анализов из стандартного OData 1С.

    Показатели шаблона сопоставляются со справочником (IndicatorLibrary) по GUID
    (external_id). Если показатель не найден:
      - create_missing_indicators=False (по умолчанию) — показатель пропускается и
        его GUID добавляется в result["missing_indicators"] (сначала импортируйте
        справочник показателей);
      - create_missing_indicators=True — создаётся заглушка показателя.

    variants_endpoint — путь к справочнику вариантов (ДопАналитика); если задан,
    строится карта GUID→текст для нечисловых норм (ЭталонОт/ЭталонДо-ссылок).
    """
    service = OneCIntegrationService(config)
    result: Dict[str, Any] = {
        "total": 0, "created": 0, "updated": 0, "skipped": 0,
        "missing_indicators": [], "errors": [],
        "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        # Карта вариантов (для нечисловых норм): GUID варианта -> текст
        variant_map: Dict[str, str] = {}
        if variants_endpoint:
            try:
                vrows = await service._fetch_list(variants_endpoint, params={"$format": "json"}, key="value")
                for v in vrows:
                    rk = v.get("Ref_Key")
                    dsc = (v.get("Description") or "").strip()
                    if rk and dsc:
                        variant_map[str(rk).lower()] = dsc
                logger.info(f"OData: карта вариантов норм — {len(variant_map)} значений")
            except Exception as e:
                logger.warning(f"Не удалось загрузить варианты для нечисловых норм: {e}")

        # 1С OData отдаёт XML по умолчанию — запрашиваем JSON и берём массив из "value"
        raw = await service._fetch_list(endpoint, params={"$format": "json"}, key="value")
        # Отсекаем группы и помеченные на удаление
        templates = [
            t for t in raw
            if not t.get("IsFolder") and not t.get("DeletionMark")
        ]
        result["total"] = len(templates)
        logger.info(f"OData: получено {len(raw)} записей, шаблонов к импорту {len(templates)}")

        # Индекс справочника по GUID (external_id)
        lib_by_guid: Dict[str, IndicatorLibrary] = {}
        for ind in db.query(IndicatorLibrary).all():
            if ind.external_id:
                lib_by_guid[str(ind.external_id).lower()] = ind

        missing: set = set()

        for tpl in templates:
            try:
                local = transform_1c_odata_template_to_local(
                    tpl, indicators_field, norms_field, indicator_key_field, name_field,
                    variant_map=variant_map,
                )
                if not local:
                    result["skipped"] += 1
                    continue

                ext_id = local.get("external_id")
                existing = None
                if ext_id:
                    existing = db.query(AnalysisType).filter(
                        AnalysisType.external_id == ext_id
                    ).first()
                if existing is None:
                    existing = db.query(AnalysisType).filter(
                        AnalysisType.name == local["name"]
                    ).first()

                if existing and skip_duplicates:
                    result["skipped"] += 1
                    continue

                if existing:
                    tmpl_obj = existing
                    tmpl_obj.description = local.get("description") or tmpl_obj.description
                    tmpl_obj.is_active = local.get("is_active", True)
                    tmpl_obj.external_id = ext_id
                    for ti in list(tmpl_obj.template_indicators):
                        db.delete(ti)
                    db.flush()
                    result["updated"] += 1
                else:
                    tmpl_obj = AnalysisType(
                        name=local["name"],
                        description=local.get("description"),
                        created_by=user_id,
                        is_active=local.get("is_active", True),
                        external_id=ext_id,
                    )
                    db.add(tmpl_obj)
                    db.flush()
                    result["created"] += 1

                for li in local["library_indicators"]:
                    guid = str(li["indicator_external_id"]).lower()
                    ind = lib_by_guid.get(guid)
                    if ind is None:
                        if create_missing_indicators:
                            ind = IndicatorLibrary(
                                name=f"Показатель {li['indicator_external_id']}",
                                data_type="number",
                                external_id=li["indicator_external_id"],
                                created_by=user_id,
                            )
                            db.add(ind)
                            db.flush()
                            lib_by_guid[guid] = ind
                        else:
                            missing.add(li["indicator_external_id"])
                            continue
                    ti = TemplateIndicator(
                        template_id=tmpl_obj.id,
                        indicator_id=ind.id,
                        min_value=li.get("min_value"),
                        max_value=li.get("max_value"),
                        norm_text=li.get("norm_text"),
                        sort_order=li.get("sort_order", 0),
                        external_id=li.get("external_id"),
                    )
                    db.add(ti)

            except Exception as e:
                logger.error(f"OData template error: {e}")
                result["errors"].append({"template": tpl.get(name_field), "error": str(e)})

        result["missing_indicators"] = sorted(missing)
        db.commit()
        logger.info(
            f"OData templates import: {result['created']} created, {result['updated']} updated, "
            f"{result['skipped']} skipped, {len(result['missing_indicators'])} missing indicators, "
            f"{len(result['errors'])} errors"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"OData templates import failed: {str(e)}")
        result["errors"].append({"error": str(e)})
        raise
    finally:
        await service.close()
    return result


async def import_plans_from_1c(
    db: Session,
    config: ExternalSystemConfig,
    endpoint: str = "/api/v1/analysis-plans",
    field_mapping: Optional[Dict[str, str]] = None,
    skip_duplicates: bool = True,
    user_id: int = 1,
) -> Dict[str, Any]:
    """
    Импортировать планы анализов из 1С в локальную БД.
    
    Returns:
        {
            "total": 5,
            "created": 3,
            "skipped": 2,
            "errors": []
        }
    """
    service = OneCIntegrationService(config)
    result = {
        "total": 0, "created": 0, "skipped": 0,
        "errors": [], "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        plans_1c = await service.fetch_plans_from_1c(endpoint)
        result["total"] = len(plans_1c)
        logger.info(f"Fetched {len(plans_1c)} plans from 1C")

        for plan_data in plans_1c:
            try:
                local_data = transform_1c_plan_to_local(plan_data, field_mapping)
                if local_data is None:
                    result["errors"].append({"plan": plan_data, "error": "Failed to transform"})
                    continue

                # Проверяем существование по имени + дате
                existing = db.query(AnalysisPlan).filter(
                    AnalysisPlan.name == local_data["name"],
                    AnalysisPlan.plan_date == local_data["plan_date"],
                ).first()

                if existing:
                    if skip_duplicates:
                        result["skipped"] += 1
                        continue
                    # Обновляем — удаляем старые items, создаём новые
                    for item in existing.plan_items:
                        db.delete(item)
                    db.flush()
                    for item_data in local_data.get("plan_items", []):
                        item = PlanItem(
                            plan_id=existing.id,
                            template_id=item_data["template_id"],
                            batch_number=item_data.get("batch_number", ""),
                            sort_order=item_data.get("sort_order", 0),
                        )
                        db.add(item)
                else:
                    # Создаём новый план
                    db_plan = AnalysisPlan(
                        name=local_data["name"],
                        description=local_data.get("description"),
                        plan_date=local_data["plan_date"],
                        created_by=user_id,
                    )
                    db.add(db_plan)
                    db.flush()
                    for item_data in local_data.get("plan_items", []):
                        item = PlanItem(
                            plan_id=db_plan.id,
                            template_id=item_data["template_id"],
                            batch_number=item_data.get("batch_number", ""),
                            sort_order=item_data.get("sort_order", 0),
                        )
                        db.add(item)
                    result["created"] += 1

            except Exception as e:
                logger.error(f"Error processing plan: {e}")
                result["errors"].append({"plan": plan_data, "error": str(e)})

        db.commit()
        logger.info(
            f"Plans import: {result['created']} created, "
            f"{result['skipped']} skipped, {len(result['errors'])} errors"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Plans import failed: {str(e)}")
        result["errors"].append({"error": str(e)})
        raise
    finally:
        await service.close()


# ==================== Сорта (справочник) через OData ====================

def transform_1c_odata_variety_to_local(
    variety_1c: Dict[str, Any],
    name_field: str = "Description",
    code_field: str = "Code",
) -> Optional[Dict[str, Any]]:
    """Преобразовать элемент справочника сортов из стандартного OData 1С в локальный формат.

    - name        <- Description (name_field)
    - code        <- Code (code_field)
    - external_id <- Ref_Key (GUID)
    Группы (IsFolder) и помеченные на удаление (DeletionMark) отсекаются до вызова.
    """
    name = variety_1c.get(name_field)
    if not name:
        return None
    ref_key = variety_1c.get("Ref_Key")
    return {
        "name": str(name).strip(),
        "code": (str(variety_1c.get(code_field)).strip() or None) if variety_1c.get(code_field) else None,
        "external_id": ref_key if (ref_key and ref_key != ZERO_GUID) else None,
        "is_active": not bool(variety_1c.get("DeletionMark")),
    }


async def import_odata_varieties_from_1c(
    db: Session,
    config: "ExternalSystemConfig",
    endpoint: str,
    skip_duplicates: bool = True,
    name_field: str = "Description",
    code_field: str = "Code",
) -> Dict[str, Any]:
    """Импортировать справочник сортов из стандартного OData 1С.

    Сопоставление по external_id (Ref_Key), фолбэк по имени. Существующие
    обновляются (если skip_duplicates=False) либо пропускаются.
    """
    from app.models import Variety

    service = OneCIntegrationService(config)
    result: Dict[str, Any] = {
        "total": 0, "created": 0, "updated": 0, "skipped": 0,
        "errors": [], "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        raw = await service._fetch_list(endpoint, params={"$format": "json"}, key="value")
        items = [v for v in raw if not v.get("IsFolder") and not v.get("DeletionMark")]
        result["total"] = len(items)
        logger.info(f"OData сорта: получено {len(raw)}, к импорту {len(items)}")

        # индексы в памяти (autoflush выключен — не полагаемся на query по имени)
        all_existing = db.query(Variety).all()
        by_guid = {str(v.external_id).lower(): v for v in all_existing if v.external_id}
        used_names = {v.name for v in all_existing}

        def _uniq_name(name: str, guid: Optional[str]) -> str:
            """Уникализировать имя при коллизии (в 1С бывают одинаковые имена)."""
            if name not in used_names:
                return name
            suffix = (guid or "")[:8] or "dup"
            cand = f"{name} [{suffix}]"
            i = 2
            while cand in used_names:
                cand = f"{name} [{suffix}-{i}]"; i += 1
            return cand

        for row in items:
            try:
                local = transform_1c_odata_variety_to_local(row, name_field, code_field)
                if not local:
                    result["skipped"] += 1
                    continue
                guid = local.get("external_id")
                gkey = str(guid).lower() if guid else None
                existing = by_guid.get(gkey) if gkey else None

                if existing and skip_duplicates:
                    result["skipped"] += 1
                    continue

                if existing:
                    new_name = local["name"]
                    if new_name != existing.name:
                        new_name = _uniq_name(new_name, guid)
                        used_names.discard(existing.name)
                        used_names.add(new_name)
                    existing.name = new_name
                    existing.code = local.get("code")
                    existing.is_active = local.get("is_active", True)
                    result["updated"] += 1
                else:
                    nm = _uniq_name(local["name"], guid)
                    v = Variety(
                        name=nm, code=local.get("code"),
                        external_id=guid, is_active=local.get("is_active", True),
                    )
                    db.add(v)
                    used_names.add(nm)
                    if gkey:
                        by_guid[gkey] = v
                    result["created"] += 1
            except Exception as e:
                logger.error(f"Error processing variety: {e}")
                result["errors"].append({"variety": row.get(name_field), "error": str(e)})

        db.commit()
        logger.info(
            f"Varieties import: {result['created']} created, "
            f"{result['updated']} updated, {result['skipped']} skipped, "
            f"{len(result['errors'])} errors"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Varieties import failed: {str(e)}")
        result["errors"].append({"error": str(e)})
        raise
    finally:
        await service.close()
    return result


# ==================== Показатели (справочник) через OData ====================

async def import_odata_indicators_from_1c(
    db: Session,
    config: "ExternalSystemConfig",
    endpoint: str,
    skip_duplicates: bool = False,
    name_field: str = "Description",
    unit_field: str = "ЕдиницаИзмерения",
    code_field: str = "Code",
) -> Dict[str, Any]:
    """Импортировать справочник показателей из стандартного OData 1С.

    Сопоставление по external_id (Ref_Key). name <- Description, unit <- unit_field
    (если это скалярное значение), external_id <- Ref_Key. Именно external_id (GUID)
    используется затем при импорте шаблонов для связи показателей.
    """
    service = OneCIntegrationService(config)
    result: Dict[str, Any] = {
        "total": 0, "created": 0, "updated": 0, "skipped": 0,
        "errors": [], "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        raw = await service._fetch_list(endpoint, params={"$format": "json"}, key="value")
        items = [i for i in raw if not i.get("IsFolder") and not i.get("DeletionMark")]
        result["total"] = len(items)
        logger.info(f"OData показатели: получено {len(raw)}, к импорту {len(items)}")

        for row in items:
            try:
                name = row.get(name_field)
                if not name:
                    result["skipped"] += 1
                    continue
                ref_key = row.get("Ref_Key")
                ext_id = ref_key if (ref_key and ref_key != ZERO_GUID) else None
                unit_val = row.get(unit_field)
                unit = str(unit_val).strip() if isinstance(unit_val, (str, int, float)) and str(unit_val).strip() else None

                existing = None
                if ext_id:
                    existing = db.query(IndicatorLibrary).filter(
                        IndicatorLibrary.external_id == ext_id
                    ).first()
                if existing is None:
                    existing = db.query(IndicatorLibrary).filter(
                        IndicatorLibrary.name == str(name).strip()
                    ).first()

                if existing and skip_duplicates:
                    result["skipped"] += 1
                    continue

                if existing:
                    existing.name = str(name).strip()
                    if unit:
                        existing.unit = unit
                    existing.external_id = ext_id or existing.external_id
                    result["updated"] += 1
                else:
                    db.add(IndicatorLibrary(
                        name=str(name).strip(),
                        unit=unit,
                        data_type="number",
                        external_id=ext_id,
                    ))
                    result["created"] += 1
            except Exception as e:
                logger.error(f"Error processing indicator: {e}")
                result["errors"].append({"indicator": row.get(name_field), "error": str(e)})

        db.commit()
        logger.info(
            f"Indicators import (OData): {result['created']} created, "
            f"{result['updated']} updated, {result['skipped']} skipped, "
            f"{len(result['errors'])} errors"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Indicators OData import failed: {str(e)}")
        result["errors"].append({"error": str(e)})
        raise
    finally:
        await service.close()
    return result


# ==================== Планы анализов через OData ====================

async def import_odata_plans_from_1c(
    db: Session,
    config: "ExternalSystemConfig",
    endpoint: str,
    skip_duplicates: bool = True,
    user_id: int = 1,
    name_field: str = "Number",
    date_field: str = "Date",
    items_field: str = "СоставАнализов",
    template_key_field: str = "ТиповойАнализ_Key",
    batch_field: str = "Серия",
) -> Dict[str, Any]:
    """Импортировать планы анализов из стандартного OData 1С (документ с табличной частью).

    Шаблоны позиций сопоставляются со справочником AnalysisType по external_id (GUID).
    Поля документа настраиваются (по умолчанию — типичные имена ERP). Требует
    предварительного импорта шаблонов из 1С.
    """
    service = OneCIntegrationService(config)
    result: Dict[str, Any] = {
        "total": 0, "created": 0, "updated": 0, "skipped": 0,
        "errors": [], "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        raw = await service._fetch_list(endpoint, params={"$format": "json"}, key="value")
        docs = [d for d in raw if not d.get("DeletionMark")]
        result["total"] = len(docs)
        logger.info(f"OData планы: получено {len(raw)}, к импорту {len(docs)}")

        # индекс шаблонов по GUID
        tpl_by_guid: Dict[str, AnalysisType] = {}
        for t in db.query(AnalysisType).all():
            if t.external_id:
                tpl_by_guid[str(t.external_id).lower()] = t

        for doc in docs:
            try:
                name = doc.get(name_field) or doc.get("Description")
                if not name:
                    result["skipped"] += 1
                    continue
                ref_key = doc.get("Ref_Key")
                ext_id = ref_key if (ref_key and ref_key != ZERO_GUID) else None

                existing = None
                if ext_id:
                    existing = db.query(AnalysisPlan).filter(
                        AnalysisPlan.external_id == ext_id
                    ).first() if hasattr(AnalysisPlan, "external_id") else None
                if existing and skip_duplicates:
                    result["skipped"] += 1
                    continue

                date_raw = doc.get(date_field)
                try:
                    plan_date = date.fromisoformat(str(date_raw)[:10]) if date_raw else date.today()
                except Exception:
                    plan_date = date.today()

                plan = AnalysisPlan(
                    name=str(name),
                    plan_date=plan_date,
                    created_by=user_id,
                )
                if hasattr(plan, "external_id"):
                    plan.external_id = ext_id
                db.add(plan)
                db.flush()

                for idx, row in enumerate(doc.get(items_field, []) or []):
                    guid = str(row.get(template_key_field, "")).lower()
                    tpl = tpl_by_guid.get(guid)
                    if not tpl:
                        continue
                    db.add(PlanItem(
                        plan_id=plan.id,
                        template_id=tpl.id,
                        batch_number=str(row.get(batch_field, "") or ""),
                        sort_order=idx,
                    ))
                result["created"] += 1
            except Exception as e:
                logger.error(f"Error processing plan: {e}")
                result["errors"].append({"plan": doc.get(name_field), "error": str(e)})

        db.commit()
        logger.info(
            f"Plans import (OData): {result['created']} created, "
            f"{result['skipped']} skipped, {len(result['errors'])} errors"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Plans OData import failed: {str(e)}")
        result["errors"].append({"error": str(e)})
        raise
    finally:
        await service.close()
    return result

# ============ Варианты значений показателей (ДопАналитика) через OData ============

async def import_odata_indicator_options_from_1c(
    db: Session,
    config: "ExternalSystemConfig",
    endpoint: str,
    owner_field: str = "Owner_Key",
    value_field: str = "Description",
) -> Dict[str, Any]:
    """Загрузить варианты значений показателей из подчинённого справочника 1С
    (Catalog__ДопАналитикаПоказателейАнализов).

    Каждая запись — один вариант: value_field (Description) = значение,
    owner_field (Owner_Key) = GUID показателя-владельца. Группируем по владельцу,
    сопоставляем с IndicatorLibrary по external_id, пишем options (JSON) и
    data_type='select'.
    """
    import json as _json
    service = OneCIntegrationService(config)
    result: Dict[str, Any] = {
        "total": 0, "updated": 0, "options": 0, "no_match": 0,
        "errors": [], "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        rows = await service._fetch_list(endpoint, params={"$format": "json"}, key="value")
        result["total"] = len(rows)

        groups: Dict[str, list] = {}
        for r in rows:
            if r.get("DeletionMark"):
                continue
            owner = r.get(owner_field)
            val = (r.get(value_field) or "").strip()
            if not owner or str(owner) == ZERO_GUID or not val:
                continue
            groups.setdefault(str(owner).lower(), []).append((r.get("Code") or "", val))

        lib: Dict[str, IndicatorLibrary] = {}
        for ind in db.query(IndicatorLibrary).all():
            if ind.external_id:
                lib[str(ind.external_id).lower()] = ind

        for owner, items in groups.items():
            ind = lib.get(owner)
            if not ind:
                result["no_match"] += 1
                continue
            seen = set(); uniq = []
            for _code, val in sorted(items):
                if val not in seen:
                    seen.add(val); uniq.append(val)
            ind.options = _json.dumps(uniq, ensure_ascii=False)
            ind.data_type = "select"
            result["updated"] += 1
            result["options"] += len(uniq)

        db.commit()
        logger.info(
            f"Indicator options import: updated={result['updated']}, "
            f"options={result['options']}, no_match={result['no_match']}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Indicator options import failed: {str(e)}")
        result["errors"].append({"error": str(e)})
        raise
    finally:
        await service.close()
    return result


# ============ Матрица норм шаблонов (Этап 1: наполнение данных) ============

async def import_odata_template_norms_from_1c(
    db: Session,
    config: "ExternalSystemConfig",
    templates_endpoint: str,
    variants_endpoint: Optional[str] = None,
    objects_endpoint: Optional[str] = None,
    indicators_field: str = "ПоказателиАнализа",
    norms_field: str = "Нормативы",
) -> Dict[str, Any]:
    """Загрузить полную матрицу норм в таблицу template_norms.

    Источники (inline ТЧ шаблона ТиповыеАнализыСерий):
      - Нормативы: (Показатель, Характеристика=сорт, Тара, Объект) -> Минимум/Максимум
      - ПоказателиАнализа: (Показатель, День[, сорт, тара]) -> ЭталонОт/ЭталонДо, norm_text
    Сопоставление показателя по IndicatorLibrary.external_id == Показатель_Key.
    Существующие нормы шаблона перезаписываются. Поведение остального приложения не меняется.
    """
    from app.models.template_norm import TemplateNorm

    service = OneCIntegrationService(config)
    result: Dict[str, Any] = {
        "templates": 0, "norm_rows": 0, "skipped_no_indicator": 0,
        "errors": [], "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        # карты для резолва
        variant_map: Dict[str, str] = {}
        if variants_endpoint:
            try:
                for v in await service._fetch_list(variants_endpoint, params={"$format": "json"}, key="value"):
                    rk = v.get("Ref_Key"); dsc = (v.get("Description") or "").strip()
                    if rk and dsc:
                        variant_map[str(rk).lower()] = dsc
            except Exception as e:
                logger.warning(f"variants map: {e}")
        object_map: Dict[str, str] = {}
        if objects_endpoint:
            try:
                for o in await service._fetch_list(objects_endpoint, params={"$format": "json"}, key="value"):
                    rk = o.get("Ref_Key"); dsc = (o.get("Description") or "").strip()
                    if rk and dsc:
                        object_map[str(rk).lower()] = dsc
            except Exception as e:
                logger.warning(f"objects map: {e}")

        lib_by_guid: Dict[str, IndicatorLibrary] = {}
        for ind in db.query(IndicatorLibrary).all():
            if ind.external_id:
                lib_by_guid[str(ind.external_id).lower()] = ind

        raw = await service._fetch_list(templates_endpoint, params={"$format": "json"}, key="value")
        templates = [t for t in raw if not t.get("IsFolder") and not t.get("DeletionMark")]

        def _norm_key(v):
            return v if (v not in (None, "", ZERO_GUID) and str(v) != ZERO_GUID) else None

        def _ind(guid):
            g = str(guid or "").lower()
            return lib_by_guid.get(g)

        for tpl in templates:
            ext_id = tpl.get("Ref_Key")
            tmpl = None
            if ext_id:
                tmpl = db.query(AnalysisType).filter(AnalysisType.external_id == str(ext_id)).first()
            if tmpl is None:
                tmpl = db.query(AnalysisType).filter(AnalysisType.name == tpl.get("Description")).first()
            if tmpl is None:
                continue

            # очистить прежние нормы шаблона
            db.query(TemplateNorm).filter(TemplateNorm.template_id == tmpl.id).delete()
            db.flush()
            result["templates"] += 1

            # 1) Нормативы: сорт/тара/объект -> min/max (день = любой)
            for r in (tpl.get(norms_field) or []):
                ind = _ind(r.get("Показатель_Key"))
                if ind is None:
                    result["skipped_no_indicator"] += 1
                    continue
                mn = _odata_num(r.get("Минимум")); mx = _odata_num(r.get("Максимум"))
                nt_ot = _etalon_ref_text(r.get("Минимум"), r.get("Минимум_Type"), variant_map)
                nt_do = _etalon_ref_text(r.get("Максимум"), r.get("Максимум_Type"), variant_map)
                nt = (f"{nt_ot} – {nt_do}" if nt_ot and nt_do and nt_ot != nt_do else (nt_ot or nt_do))
                obj = _norm_key(r.get("ОбъектАнализа_Key"))
                db.add(TemplateNorm(
                    template_id=tmpl.id, indicator_id=ind.id, day=None,
                    variety_key=_norm_key(r.get("Характеристика_Key")),
                    container=(str(r.get("ТараДляПива")).strip() or None) if r.get("ТараДляПива") else None,
                    object_key=obj, object_name=object_map.get(str(obj).lower()) if obj else None,
                    min_value=mn, max_value=mx, norm_text=nt, source="normativy",
                ))
                result["norm_rows"] += 1

            # 2) ПоказателиАнализа: день + ЭталонОт/До
            for r in (tpl.get(indicators_field) or []):
                ind = _ind(r.get("Показатель_Key"))
                if ind is None:
                    result["skipped_no_indicator"] += 1
                    continue
                mn = _odata_num(r.get("ЭталонОт")); mx = _odata_num(r.get("ЭталонДо"))
                ot = _etalon_ref_text(r.get("ЭталонОт"), r.get("ЭталонОт_Type"), variant_map)
                do = _etalon_ref_text(r.get("ЭталонДо"), r.get("ЭталонДо_Type"), variant_map)
                nt = (f"{ot} – {do}" if ot and do and ot != do else (ot or do))
                try:
                    day = int(r.get("День")) if r.get("День") not in (None, "") else None
                except (TypeError, ValueError):
                    day = None
                db.add(TemplateNorm(
                    template_id=tmpl.id, indicator_id=ind.id, day=day,
                    variety_key=_norm_key(r.get("Характеристика_Key")),
                    container=(str(r.get("ТараДляПива")).strip() or None) if r.get("ТараДляПива") else None,
                    object_key=None, object_name=None,
                    min_value=mn, max_value=mx, norm_text=nt, source="schedule",
                ))
                result["norm_rows"] += 1

        db.commit()
        logger.info(f"Template norms: templates={result['templates']}, rows={result['norm_rows']}")
    except Exception as e:
        db.rollback()
        logger.error(f"Template norms import failed: {e}")
        result["errors"].append({"error": str(e)})
        raise
    finally:
        await service.close()
    return result


# ============ Объекты анализа/отбора (справочник) через OData ============

async def import_odata_objects_from_1c(
    db: Session,
    config: "ExternalSystemConfig",
    endpoint: str,
    name_field: str = "Description",
    code_field: str = "Code",
) -> Dict[str, Any]:
    """Импортировать справочник объектов анализа/отбора (Catalog__ОбъектыАнализа).
    Дедуп по GUID, различение дублей имён. Помеченные на удаление/группы отсекаются."""
    from app.models import AnalysisObject

    service = OneCIntegrationService(config)
    result: Dict[str, Any] = {
        "total": 0, "created": 0, "updated": 0, "skipped": 0,
        "errors": [], "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        raw = await service._fetch_list(endpoint, params={"$format": "json"}, key="value")
        items = [o for o in raw if not o.get("IsFolder") and not o.get("DeletionMark")]
        result["total"] = len(items)

        existing = db.query(AnalysisObject).all()
        by_guid = {str(o.external_id).lower(): o for o in existing if o.external_id}
        used_names = {o.name for o in existing}

        def _uniq(name, guid):
            if name not in used_names:
                return name
            base = f"{name} [{(guid or '')[:8] or 'dup'}]"
            c, i = base, 2
            while c in used_names:
                c = f"{base}-{i}"; i += 1
            return c

        for row in items:
            try:
                name = (row.get(name_field) or "").strip()
                if not name:
                    result["skipped"] += 1
                    continue
                rk = row.get("Ref_Key")
                guid = rk if (rk and rk != ZERO_GUID) else None
                gkey = str(guid).lower() if guid else None
                obj = by_guid.get(gkey) if gkey else None
                if obj:
                    if name != obj.name:
                        nm = _uniq(name, guid); used_names.discard(obj.name); used_names.add(nm)
                        obj.name = nm
                    obj.is_active = not bool(row.get("DeletionMark"))
                    result["updated"] += 1
                else:
                    nm = _uniq(name, guid)
                    o = AnalysisObject(name=nm, external_id=guid, is_active=True)
                    db.add(o); used_names.add(nm)
                    if gkey:
                        by_guid[gkey] = o
                    result["created"] += 1
            except Exception as e:
                result["errors"].append({"object": row.get(name_field), "error": str(e)})
        db.commit()
        logger.info(f"Objects import: created={result['created']} updated={result['updated']}")
    except Exception as e:
        db.rollback()
        logger.error(f"Objects import failed: {e}")
        result["errors"].append({"error": str(e)})
        raise
    finally:
        await service.close()
    return result


# ============ Варианты из справочника Склады (папка Емкости) → показатели ============

def _norm_name(s: str) -> str:
    return str(s or "").replace("ё", "е").replace("Ё", "Е").strip().lower()

# Правила по умолчанию: какой показатель наполнять из какой папки Складов
DEFAULT_STORAGE_RULES = [
    {"folder": ["Емкости"], "indicator": "Номер ёмкости"},
    {"folder": ["Емкости", "Танки"], "indicator": "Номер танка"},
]


async def import_odata_storage_options_from_1c(
    db: Session,
    config: "ExternalSystemConfig",
    endpoint: str,
    rules: Optional[list] = None,
) -> Dict[str, Any]:
    """Наполнить показатели вариантами из справочника Склады (иерархия).

    Для каждого правила {folder: [путь папок], indicator: имя показателя}
    собираем все элементы (рекурсивно) под указанной папкой и записываем их
    в options показателя (+ data_type='select'). Сопоставление показателя по
    имени без учёта регистра и ё/е.
    """
    import json as _json
    from app.models import IndicatorLibrary

    rules = rules or DEFAULT_STORAGE_RULES
    service = OneCIntegrationService(config)
    result: Dict[str, Any] = {"rules": [], "errors": [], "timestamp": datetime.utcnow().isoformat()}
    try:
        rows = await service._fetch_list(endpoint, params={"$format": "json"}, key="value")
        await service.close()

        by_ref = {str(r.get("Ref_Key")).lower(): r for r in rows}
        children = {}
        for r in rows:
            children.setdefault(str(r.get("Parent_Key")).lower(), []).append(r)

        def find_folder(path):
            """Найти папку по пути имён; вернуть Ref_Key или None."""
            parent = None  # верхний уровень
            cur_ref = None
            for name in path:
                candidates = [
                    r for r in rows
                    if r.get("IsFolder") and _norm_name(r.get("Description")) == _norm_name(name)
                    and (cur_ref is None or str(r.get("Parent_Key")).lower() == cur_ref)
                ]
                if not candidates:
                    return None
                cur_ref = str(candidates[0].get("Ref_Key")).lower()
            return cur_ref

        def collect_leaves(folder_ref):
            """Все элементы (не папки, не удалённые) рекурсивно под папкой."""
            out = []
            stack = [folder_ref]
            while stack:
                ref = stack.pop()
                for ch in children.get(ref, []):
                    if ch.get("DeletionMark"):
                        continue
                    if ch.get("IsFolder"):
                        stack.append(str(ch.get("Ref_Key")).lower())
                    else:
                        d = (ch.get("Description") or "").strip()
                        if d:
                            out.append(d)
            return sorted(set(out))

        # индекс показателей по нормализованному имени
        lib = {}
        for ind in db.query(IndicatorLibrary).all():
            lib.setdefault(_norm_name(ind.name), ind)

        for rule in rules:
            info = {"folder": " / ".join(rule["folder"]), "indicator": rule["indicator"]}
            fref = find_folder(rule["folder"])
            if not fref:
                info["status"] = "папка не найдена"
                result["rules"].append(info); continue
            leaves = collect_leaves(fref)
            ind = lib.get(_norm_name(rule["indicator"]))
            if not ind:
                info["status"] = "показатель не найден"; info["values"] = len(leaves)
                result["rules"].append(info); continue
            ind.options = _json.dumps(leaves, ensure_ascii=False)
            ind.data_type = "select"
            info["status"] = "ok"; info["values"] = len(leaves)
            result["rules"].append(info)

        db.commit()
        logger.info(f"Storage options import: {result['rules']}")
    except Exception as e:
        db.rollback()
        logger.error(f"Storage options import failed: {e}")
        result["errors"].append({"error": str(e)})
        raise
    return result


# ============ Импорт РЕЗУЛЬТАТОВ анализов из 1С (документ УстановкаАнализовСерии) ============

async def import_odata_results_from_1c(
    db: Session,
    config: "ExternalSystemConfig",
    date_from: str,
    date_to: str,
    endpoint: str = "/erp_tek/odata/standard.odata/Document__УстановкаАнализовСерии",
    user_id: int = 1,
    only_posted: bool = True,
) -> Dict[str, Any]:
    """Импортировать результаты анализов за период из 1С в отчёты приложения.

    Документ УстановкаАнализовСерии → ProcessLog; строки ТЧ ПоказателиАнализа →
    IndicatorValue. Значение-ссылка (Склады/ДопАналитика) резолвится в текст.
    Идемпотентно по external_id (Ref_Key документа).
    date_from/date_to — 'YYYY-MM-DD'.
    """
    from datetime import datetime
    from app.models import (ProcessLog, IndicatorValue, IndicatorLibrary,
                            AnalysisType, Variety)
    from app.models.process_log import Status

    service = OneCIntegrationService(config)
    r: Dict[str, Any] = {
        "documents": 0, "reports_created": 0, "reports_updated": 0, "values": 0,
        "skipped_no_template": 0, "skipped_no_indicator": 0, "errors": [],
        "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        base = "/erp_tek/odata/standard.odata/"
        ind_by_guid = {str(i.external_id).lower(): i for i in db.query(IndicatorLibrary).all() if i.external_id}
        tpl_by_guid = {str(t.external_id).lower(): t for t in db.query(AnalysisType).all() if t.external_id}
        var_by_guid = {str(v.external_id).lower(): v.name for v in db.query(Variety).all() if v.external_id}

        # карты значений-ссылок (Склады, ДопАналитика)
        sklady = {}
        for row in await service._fetch_list(base + "Catalog_Склады", params={"$format": "json"}, key="value"):
            rk = row.get("Ref_Key"); d = (row.get("Description") or "").strip()
            if rk and d:
                sklady[str(rk).lower()] = d
        dop = {}
        for row in await service._fetch_list(base + "Catalog__ДопАналитикаПоказателейАнализов", params={"$format": "json"}, key="value"):
            rk = row.get("Ref_Key"); d = (row.get("Description") or "").strip()
            if rk and d:
                dop[str(rk).lower()] = d

        flt = f"Date ge datetime'{date_from}T00:00:00' and Date le datetime'{date_to}T23:59:59'"
        if only_posted:
            flt += " and Posted eq true"
        docs = await service._fetch_list(endpoint, params={"$format": "json", "$filter": flt}, key="value")
        await service.close()
        r["documents"] = len(docs)

        def _val(raw, vtype):
            """(numeric, text) из значения показателя по типу."""
            if raw in (None, "") or str(vtype).endswith("Undefined"):
                return None, None
            t = str(vtype or "")
            if t == "Edm.Double":
                try:
                    return float(raw), None
                except (TypeError, ValueError):
                    return None, str(raw)
            if "Склады" in t:
                return None, sklady.get(str(raw).lower(), str(raw))
            if "ДопАналитика" in t:
                return None, dop.get(str(raw).lower(), str(raw))
            return None, str(raw)

        for i, doc in enumerate(docs):
            try:
                if doc.get("DeletionMark"):
                    continue
                tpl = tpl_by_guid.get(str(doc.get("ТиповойАнализ_Key")).lower())
                if not tpl:
                    r["skipped_no_template"] += 1
                    continue
                ext = doc.get("Ref_Key")
                try:
                    started = datetime.fromisoformat(str(doc.get("Date"))[:19])
                except Exception:
                    started = datetime.utcnow()
                skey = doc.get("СерияНоменклатуры")
                skey = skey if (skey and skey != ZERO_GUID) else None
                variety = var_by_guid.get(str(doc.get("Характеристика_Key")).lower())
                container = (str(doc.get("ТараДляПива")).strip() or None) if doc.get("ТараДляПива") else None

                pl = db.query(ProcessLog).filter(ProcessLog.external_id == ext).first() if ext else None
                if pl:
                    db.query(IndicatorValue).filter(IndicatorValue.process_log_id == pl.id).delete()
                    r["reports_updated"] += 1
                else:
                    pl = ProcessLog(created_by=user_id)
                    db.add(pl)
                    r["reports_created"] += 1
                pl.batch_number = doc.get("СерияНоменклатуры2") or ""
                pl.series_key = skey
                pl.variety = variety
                pl.container = container
                pl.analysis_type_id = tpl.id
                pl.started_at = started
                pl.status = Status.COMPLETED
                pl.external_id = ext
                db.flush()

                for row in (doc.get("ПоказателиАнализа") or []):
                    ind = ind_by_guid.get(str(row.get("Показатель_Key")).lower())
                    if not ind:
                        r["skipped_no_indicator"] += 1
                        continue
                    numeric, textv = _val(row.get("ЗначениеПоказателя"), row.get("ЗначениеПоказателя_Type"))
                    if numeric is None and not textv:
                        continue  # значение не внесено
                    try:
                        code = int(row.get("ЕстьОтклонение") or 0)
                    except (TypeError, ValueError):
                        code = 0
                    try:
                        day = int(row.get("День") or 0)
                    except (TypeError, ValueError):
                        day = 0
                    db.add(IndicatorValue(
                        process_log_id=pl.id, indicator_id=ind.id,
                        value=numeric, text_value=textv, day=day,
                        is_normal=(code != 2), deviation_code=code,
                        external_id=row.get("Ref_Key"),
                    ))
                    r["values"] += 1

                if i % 100 == 0:
                    db.commit()
            except Exception as e:
                r["errors"].append({"doc": doc.get("Number"), "error": str(e)[:200]})

        db.commit()
        logger.info(f"Results import: {r['reports_created']} created, {r['reports_updated']} updated, {r['values']} values")
    except Exception as e:
        db.rollback()
        logger.error(f"Results import failed: {e}")
        r["errors"].append({"error": str(e)})
        raise
    finally:
        await service.close()
    return r
