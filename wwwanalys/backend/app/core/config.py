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
    # AI-ассистент (эксперт-пивовар) для разбора отклонений — ДОПОЛНИТЕЛЬНЫЙ модуль.
    # ai_enabled: главный выключатель. False — модуль полностью выключен, интерфейс
    #   не показывает кнопку, эндпоинты недоступны, на основные функции не влияет.
    ai_enabled: bool = True
    # ai_provider: "auto" | "none" | "anthropic" (далее можно добавить ollama, gigachat, yandexgpt)
    #   "auto" — выбрать провайдер по наличию ключа/настроек; иначе работает только
    #            детерминированный движок отклонений (без текстового разбора моделью).
    ai_provider: str = "auto"
    ai_model: str = "claude-opus-4-8"
    ai_max_tokens: int = 2000
    # Ключи/адреса провайдеров (заполняются, когда выбрана конкретная модель)
    anthropic_api_key: str = ""
    # OpenRouter (OpenAI-совместимый шлюз ко многим моделям, включая Claude).
    #   Если задан openrouter_api_key — агент идёт через OpenRouter (function-calling
    #   для RAG + встроенный веб-плагин для внешних источников).
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-opus-4-8"

    # RAG / база знаний техкарт (загрузка из файлов, вектор-готовое хранилище).
    #   rag_embedding_provider: "none" пока модель не выбрана (поиск идёт по FTS);
    #   далее добавляются ollama/gigachat/voyage и т.п.
    rag_embedding_provider: str = "none"
    embedding_dim: int = 1024          # размерность вектора (bge-m3=1024, nomic=768, …)
    rag_chunk_size: int = 1000         # символов во фрагменте
    rag_chunk_overlap: int = 150       # перекрытие фрагментов
    rag_max_upload_mb: int = 25        # лимит размера файла

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()