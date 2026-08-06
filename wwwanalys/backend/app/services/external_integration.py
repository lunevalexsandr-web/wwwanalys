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


def transform_1c_odata_template_to_local(
    template_1c: Dict[str, Any],
    indicators_field: str = "ПоказателиАнализа",
    norms_field: str = "Нормативы",
    indicator_key_field: str = "Показатель_Key",
    name_field: str = "Description",
) -> Optional[Dict[str, Any]]:
    """
    Преобразовать шаблон из стандартного OData 1С (справочник ТиповыеАнализыСерий)
    в локальный формат.

    - name          <- Description
    - external_id   <- Ref_Key (GUID шаблона)
    - показатели    <- табличная часть `ПоказателиАнализа` (ссылка Показатель_Key = GUID)
    - мин/макс      <- табличная часть `Нормативы` (Минимум/Максимум по Показатель_Key),
                       фолбэк на ЭталонОт/ЭталонДо из строки показателя
    Группы (IsFolder) и помеченные на удаление (DeletionMark) должны отсекаться ДО вызова.
    """
    name = template_1c.get(name_field)
    if not name:
        return None

    ref_key = template_1c.get("Ref_Key")

    # Нормы: Показатель_Key -> (min, max)
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
        nmin, nmax = norms_map.get(str(key), (None, None))
        if nmin is None:
            nmin = _odata_num(row.get("ЭталонОт"))
        if nmax is None:
            nmax = _odata_num(row.get("ЭталонДо"))
        library_indicators.append({
            "indicator_external_id": str(key),
            "external_id": str(key),
            "min_value": nmin,
            "max_value": nmax,
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
) -> Dict[str, Any]:
    """
    Импортировать шаблоны анализов из стандартного OData 1С.

    Показатели шаблона сопоставляются со справочником (IndicatorLibrary) по GUID
    (external_id). Если показатель не найден:
      - create_missing_indicators=False (по умолчанию) — показатель пропускается и
        его GUID добавляется в result["missing_indicators"] (сначала импортируйте
        справочник показателей);
      - create_missing_indicators=True — создаётся заглушка показателя.
    """
    service = OneCIntegrationService(config)
    result: Dict[str, Any] = {
        "total": 0, "created": 0, "updated": 0, "skipped": 0,
        "missing_indicators": [], "errors": [],
        "timestamp": datetime.utcnow().isoformat(),
    }
    try:
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
                    tpl, indicators_field, norms_field, indicator_key_field, name_field
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

        for row in items:
            try:
                local = transform_1c_odata_variety_to_local(row, name_field, code_field)
                if not local:
                    result["skipped"] += 1
                    continue

                existing = None
                if local.get("external_id"):
                    existing = db.query(Variety).filter(
                        Variety.external_id == local["external_id"]
                    ).first()
                if existing is None:
                    existing = db.query(Variety).filter(Variety.name == local["name"]).first()

                if existing and skip_duplicates:
                    result["skipped"] += 1
                    continue

                if existing:
                    existing.name = local["name"]
                    existing.code = local.get("code")
                    existing.external_id = local.get("external_id") or existing.external_id
                    existing.is_active = local.get("is_active", True)
                    result["updated"] += 1
                else:
                    db.add(Variety(
                        name=local["name"],
                        code=local.get("code"),
                        external_id=local.get("external_id"),
                        is_active=local.get("is_active", True),
                    ))
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