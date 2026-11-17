"""
Application configuration

This module exposes a singleton `settings` instance that can be imported
throughout the project (e.g., from config import settings).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataAPISettings(BaseSettings):
    # Load .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # FastAPI application
    APP_NAME: str = "DataAPI"
    APP_DESCRIPTION: str = "Expose database product data to website and external services"
    APP_VERSION: str = "1.0"
    # API url infos: api.fcpxstudio.shop/<API_NAME>/<API_VERSION>/
    API_NAME: str = "data"
    API_VERSION: str = "v1" 



settings = DataAPISettings() # type: ignore