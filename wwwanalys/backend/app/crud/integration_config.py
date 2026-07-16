"""CRUD-операции для конфигурации внешних интеграций."""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.integration_config import IntegrationConfig
from app.schemas.integration_config import IntegrationConfigUpdate


def get_by_name(db: Session, name: str) -> Optional[IntegrationConfig]:
    """Получить конфигурацию по имени (например, '1c')."""
    return db.query(IntegrationConfig).filter(IntegrationConfig.name == name).first()


def upsert(db: Session, name: str, data: IntegrationConfigUpdate) -> IntegrationConfig:
    """
    Создать или обновить конфигурацию по имени.
    Пароль обновляется только если передан (не пустой).
    """
    config = get_by_name(db, name)
    payload = data.model_dump(exclude_unset=True)

    if "password" in payload and not payload["password"]:
        del payload["password"]

    if config is None:
        config = IntegrationConfig(name=name)
        db.add(config)

    for key, value in payload.items():
        setattr(config, key, value)

    db.commit()
    db.refresh(config)
    return config