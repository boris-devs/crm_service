import hashlib
from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ASYNC_PG_SCHEME = "postgresql+asyncpg://"
_SYNC_PG_SCHEMES = ("postgres://", "postgresql://")


class BotMode(StrEnum):
    POLLING = "polling"
    WEBHOOK = "webhook"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str = "crm"
    postgres_password: str = "crm"
    postgres_db: str = "crm"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")

    admin_username: str = "admin"
    admin_password: str = ""

    bot_token: str = ""
    bot_mode: BotMode = BotMode.POLLING
    webhook_base_url: str | None = Field(
        default=None, validation_alias=AliasChoices("WEBHOOK_BASE_URL", "RENDER_EXTERNAL_URL")
    )
    webhook_secret_override: str | None = Field(default=None, alias="WEBHOOK_SECRET")
    bot_services: Annotated[list[str], NoDecode] = ["Сайт", "Реклама", "SMM", "Дизайн", "Другое"]

    @field_validator("bot_services", mode="before")
    @classmethod
    def _split_services(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("database_url_override")
    @classmethod
    def _use_async_driver(cls, value: str | None) -> str | None:
        for scheme in _SYNC_PG_SCHEMES:
            if value and value.startswith(scheme):
                return ASYNC_PG_SCHEME + value.removeprefix(scheme)
        return value

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        return (
            f"{ASYNC_PG_SCHEME}{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def webhook_secret(self) -> str:
        return self.webhook_secret_override or hashlib.sha256(self.bot_token.encode()).hexdigest()


@lru_cache
def get_settings() -> Settings:
    return Settings()
