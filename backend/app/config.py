from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "Asset Aggregator API"
    app_version: str = "1.0.0"
    debug: bool = False

    database_url: str = Field(default=f"sqlite+aiosqlite:///{BASE_DIR}/data/app.db")

    secret_key: str = Field(default="change-this-in-production-use-openssl-rand-hex-32")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    alphavantage_base_url: str = "https://www.alphavantage.co/query"
    alphavantage_api_key: str = Field(default="demo")

    cache_ttl_seconds: int = 300
    cache_max_size: int = 1000

    scheduler_refresh_interval_minutes: int = 5

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
