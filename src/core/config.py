from __future__ import annotations

import os
import socket
from functools import lru_cache
from typing import Literal

try:
    import tomllib 
except ModuleNotFoundError:
    import tomli as tomllib 

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


EnvName = Literal["dev", "test", "prod"]


class Settings(BaseSettings):

    app_name: str = Field(default="be-auth")
    app_version: str = Field(default="0.1.0")
    env: EnvName = Field(default="dev", description="Runtime environment")
    enable_docs: bool = Field(default=True, description="Enable /docs and OpenAPI in non-prod")
    alembic_database_url: str | None = Field(default=None, description="Sync DSN for Alembic")

    # --- HTTP ---
    http_host: str = Field(default="0.0.0.0")
    http_port: int = Field(default=8000)
    reload: bool = Field(default=False, description="Uvicorn reload (dev only)")

    # --- CORS ---
    cors_allow_origins: str = Field(default="*")

    # --- Logging ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # --- Database ---
    database_url: str = Field(
        default="sqlite+aiosqlite:///./app.db",
        description="SQLAlchemy async URL, e.g. postgresql+asyncpg://user:pass@host:5432/db",
    )
    sql_echo: bool = Field(default=False)

    # --- Redis ---
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for session storage and caching",
    )

    # --- JWT ---
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT token signing",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration time in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration time in days"
    )

    # --- Observability / Meta ---
    public_base_url: AnyHttpUrl | None = None
    hostname: str = Field(default_factory=socket.gethostname)

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")

    @classmethod
    def from_toml(cls, path: str) -> "Settings":
        with open(path, "rb") as f:
            data = tomllib.load(f)
        flat: dict = {}
        for k, v in data.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    flat[f"{kk}"] = vv
            else:
                flat[k] = v
        return cls(**flat)


@lru_cache
def load_settings() -> Settings:
    config_file = os.getenv("CONFIG_FILE") or os.getenv("APP_CONFIG")
    base = Settings()
    if config_file and os.path.exists(config_file):
        file_settings = Settings.from_toml(config_file)
        merged = file_settings.model_copy(update=base.model_dump(exclude_unset=True))
        merged.cors_allow_origins = _parse_cors_origins(
            os.getenv("CORS_ALLOW_ORIGINS") or ",".join(file_settings.cors_allow_origins)
        )
        return merged

    base.cors_allow_origins = _parse_cors_origins(os.getenv("CORS_ALLOW_ORIGINS"))
    return base


def _parse_cors_origins(raw: str | None) -> list[str]:
    if not raw:
        return ["*"]
    if raw == "*":
        return ["*"]
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts or ["*"]
