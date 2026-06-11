"""
Сервис для интеграции с внешними системами (1С Предприятие и др.)
Поддерживает импорт справочника показателей из внешних источников.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.models import IndicatorLibrary
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
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.username = username
        self.password = password
        self.timeout = timeout


class OneCIntegrationService:
    """
    Сервис для интеграции с 1С Предприятие.
    
    Поддерживает:
    - Загрузку справочника показателей из 1С
    - Синхронизацию данных
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
            )
        return self._client

    async def close(self):
        """Закрыть HTTP-клиент."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def fetch_indicators_from_1c(
        self,
        endpoint: str = "/api/v1/indicators",
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Загрузить список показателей из 1С.
        
        Args:
            endpoint: API-эндпоинт в 1С для получения показателей
            params: Дополнительные параметры запроса
            
        Returns:
            Список показателей в формате 1С
            
        Raises:
            httpx.HTTPError: При ошибке HTTP-запроса
            ValueError: При невалидном ответе
        """
        client = await self._get_client()
        
        try:
            response = await client.get(endpoint, params=params or {})
            response.raise_for_status()
            
            data = response.json()
            
            # Поддержка разных форматов ответа от 1С
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Стандартный формат 1С: { "items": [...] }
                if "items" in data:
                    return data["items"]
                elif "data" in data:
                    return data["data"]
                elif "indicators" in data:
                    return data["indicators"]
                else:
                    # Возможно, вернулся один объект
                    return [data]
            else:
                raise ValueError(f"Unexpected response format: {type(data)}")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching indicators from 1C: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error fetching indicators from 1C: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching indicators from 1C: {str(e)}")
            raise

    async def fetch_indicator_by_id_from_1c(
        self,
        indicator_id: str,
        endpoint_prefix: str = "/api/v1/indicators",
    ) -> Optional[Dict[str, Any]]:
        """
        Загрузить один показатель из 1С по ID.
        
        Args:
            indicator_id: ID показателя в системе 1С
            endpoint_prefix: Префикс API-эндпоинта
            
        Returns:
            Данные показателя или None, если не найден
        """
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

    async def test_connection(self) -> Dict[str, Any]:
        """
        Проверить подключение к 1С.
        
        Returns:
            Словарь с результатом проверки:
            - status: "ok" или "error"
            - message: Описание результата
            - timestamp: Время проверки
        """
        client = await self._get_client()
        
        try:
            # Пробуем выполнить простой запрос
            response = await client.get("/api/v1/health", timeout=10)
            
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


def transform_1c_indicator_to_local(
    indicator_1c: Dict[str, Any],
    field_mapping: Optional[Dict[str, str]] = None,
) -> Optional[BatchCreateItem]:
    """
    Преобразовать показатель из формата 1С в локальный формат.
    
    Args:
        indicator_1c: Данные показателя из 1С
        field_mapping: Маппинг полей {local_field: 1c_field}
        
    Returns:
        BatchCreateItem для создания в локальной БД или None если данные невалидны
    """
    # Маппинг полей по умолчанию
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
        # Извлекаем имя (обязательное поле)
        name = indicator_1c.get(mapping.get("name", "name"))
        if not name:
            logger.warning(f"Indicator without name: {indicator_1c}")
            return None
        
        # Преобразуем данные
        result = {"name": name}
        
        if "unit" in mapping:
            result["unit"] = indicator_1c.get(mapping["unit"])
        
        if "data_type" in mapping:
            data_type_1c = indicator_1c.get(mapping["data_type"], "number")
            # Преобразуем типы данных из 1С в локальные
            data_type_mapping = {
                "number": "number",
                "numeric": "number",
                "integer": "number",
                "string": "text",
                "text": "text",
                "boolean": "number",  # 1С boolean -> локальный number
                "select": "select",
                "enum": "select",
            }
            result["data_type"] = data_type_mapping.get(
                str(data_type_1c).lower(), "number"
            )
        
        if "description" in mapping:
            result["description"] = indicator_1c.get(mapping["description"])
        
        if "category" in mapping:
            result["category"] = indicator_1c.get(mapping["category"])
        
        if "is_required" in mapping:
            is_required = indicator_1c.get(mapping["is_required"], False)
            result["is_required"] = bool(is_required)
        
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


async def import_indicators_from_1c(
    db: Session,
    config: ExternalSystemConfig,
    endpoint: str = "/api/v1/indicators",
    field_mapping: Optional[Dict[str, str]] = None,
    skip_duplicates: bool = True,
) -> Dict[str, Any]:
    """
    Импортировать показатели из 1С в локальную БД.
    
    Args:
        db: SQLAlchemy сессия
        config: Конфигурация подключения к 1С
        endpoint: API-эндпоинт для получения показателей
        field_mapping: Маппинг полей {local_field: 1c_field}
        skip_duplicates: Пропускать дубликаты (по имени)
        
    Returns:
        Словарь с результатами импорта:
        - total: Всего получено из 1С
        - created: Создано новых
        - skipped: Пропущено (дубликаты)
        - errors: Ошибки
    """
    service = OneCIntegrationService(config)
    
    result = {
        "total": 0,
        "created": 0,
        "skipped": 0,
        "errors": [],
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    try:
        # Загружаем показатели из 1C
        indicators_1c = await service.fetch_indicators_from_1c(endpoint)
        result["total"] = len(indicators_1c)
        
        logger.info(f"Fetched {len(indicators_1c)} indicators from 1C")
        
        # Получаем существующие имена для проверки дубликатов
        existing_names = set()
        if skip_duplicates:
            existing = db.query(IndicatorLibrary.name).all()
            existing_names = {row[0] for row in existing}
        
        # Обрабатываем каждый показатель
        for indicator_data in indicators_1c:
            try:
                # Преобразуем формат
                local_item = transform_1c_indicator_to_local(
                    indicator_data, field_mapping
                )
                
                if local_item is None:
                    result["errors"].append({
                        "indicator": indicator_data,
                        "error": "Failed to transform indicator",
                    })
                    continue
                
                # Проверяем дубликаты
                if skip_duplicates and local_item.name in existing_names:
                    result["skipped"] += 1
                    continue
                
                # Создаём показатель в локальной БД
                db_indicator = IndicatorLibrary(
                    name=local_item.name,
                    unit=local_item.unit,
                    data_type=local_item.data_type,
                    options=",".join(local_item.options) if local_item.options else None,
                    description=local_item.description,
                    category=local_item.category,
                    is_required=local_item.is_required,
                    default_value=local_item.default_value,
                    validation_rules=local_item.validation_rules,
                )
                db.add(db_indicator)
                result["created"] += 1
                existing_names.add(local_item.name)
                
            except Exception as e:
                logger.error(f"Error processing indicator: {e}")
                result["errors"].append({
                    "indicator": indicator_data,
                    "error": str(e),
                })
        
        # Сохраняем изменения
        db.commit()
        
        logger.info(
            f"Import completed: {result['created']} created, "
            f"{result['skipped']} skipped, {len(result['errors'])} errors"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Import failed: {str(e)}")
        result["errors"].append({"error": str(e)})
        raise
    finally:
        await service.close()
    
    return result