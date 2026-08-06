from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    database_url: str = "sqlite:///./test.db"
    secret_key: str = "change-me-to-a-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: str = "*"
    api_key: str = "change-me-api-key"
    # AI-ассистент (эксперт-пивовар) для разбора отклонений.
    # ai_provider: "auto" | "none" | "anthropic" (далее можно добавить ollama, gigachat, yandexgpt)
    #   "auto" — выбрать провайдер по наличию ключа/настроек; иначе работает только
    #            детерминированный движок отклонений (без текстового разбора моделью).
    ai_provider: str = "auto"
    ai_model: str = "claude-opus-4-8"
    ai_max_tokens: int = 2000
    # Ключи/адреса провайдеров (заполняются, когда выбрана конкретная модель)
    anthropic_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()