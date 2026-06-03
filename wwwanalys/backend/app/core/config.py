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

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()