"""Модель для хранения конфигурации внешних интеграций (например, 1С)."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class IntegrationConfig(Base):
    """Конфигурация подключения к внешней системе (1С и др.)."""

    __tablename__ = "integration_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, comment="Идентификатор интеграции, напр. '1c'")
    base_url = Column(String(512), nullable=True)
    api_key = Column(String(512), nullable=True)
    username = Column(String(255), nullable=True)
    password = Column(String(512), nullable=True)
    timeout = Column(Integer, default=30, nullable=False)
    endpoint = Column(String(512), nullable=True, comment="Путь HTTP-сервиса 1С")
    verify_ssl = Column(Boolean, default=False, nullable=False, comment="Проверять SSL-сертификат")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<IntegrationConfig(id={self.id}, name='{self.name}')>"