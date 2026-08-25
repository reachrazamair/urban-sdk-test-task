from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://urbansdk:urbansdk@localhost:5432/urbansdk"
    mapbox_token: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
