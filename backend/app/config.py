from __future__ import annotations

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FairHire"
    database_url: str = "sqlite:///./resume_matcher.db"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    auth_secret_key: str = "change-me-in-production"
    auth_allow_test_header: bool = False
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_sms_from: Optional[str] = None
    twilio_whatsapp_from: Optional[str] = None
    whatsapp_cloud_access_token: Optional[str] = None
    whatsapp_cloud_phone_number_id: Optional[str] = None
    whatsapp_cloud_api_version: str = "v24.0"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "fairhire-job-imports"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
