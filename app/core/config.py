from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5432/inventory_db"
    app_name: str = "Inventory Management System"
    debug: bool = False
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    low_stock_threshold: int = 10

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Managed hosts (Render, Heroku) often expose a "postgres://" URL, but
        # SQLAlchemy 2.0 requires the "postgresql://" dialect scheme.
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql://", 1)
        return value

    @property
    def origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
