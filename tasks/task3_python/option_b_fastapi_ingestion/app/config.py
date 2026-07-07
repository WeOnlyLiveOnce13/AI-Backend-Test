from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    recent_cache_size: int = Field(alias="RECENT_CACHE_SIZE")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("recent_cache_size")
    @classmethod
    def validate_recent_cache_size(cls, value: int) -> int:
        if value < 1:
            raise ValueError("RECENT_CACHE_SIZE must be at least 1")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
