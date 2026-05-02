"""
Configuração centralizada — carrega variáveis de ambiente com validação via Pydantic.
"""

from __future__ import annotations

import zoneinfo
from datetime import date
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Todas as variáveis de ambiente obrigatórias e opcionais."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── POE ──
    POE_API_KEY: str
    POE_BOT_NAME: str = "abp_tutor"

    # ── Telegram ──
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str

    # ── Supabase ──
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_USER_ID: str = ""  # auto-discover if empty

    # ── Cronograma ──
    EXAM_DATE: date
    START_DATE: date
    TIMEZONE: str = "America/Sao_Paulo"

    # ── Logging ──
    LOG_LEVEL: str = "INFO"

    @field_validator("*", mode="before")
    @classmethod
    def _strip_strings(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v

    # ── Derived ──
    @field_validator("TIMEZONE")
    @classmethod
    def _validate_timezone(cls, v: str) -> str:
        try:
            zoneinfo.ZoneInfo(v)
        except (KeyError, Exception) as exc:
            raise ValueError(f"Timezone inválida: {v}") from exc
        return v

    @property
    def tz(self) -> zoneinfo.ZoneInfo:
        return zoneinfo.ZoneInfo(self.TIMEZONE)

    @property
    def total_days(self) -> int:
        return (self.EXAM_DATE - self.START_DATE).days


@lru_cache
def get_settings() -> Settings:
    """Singleton de Settings — carregado uma vez por processo."""
    return Settings()  # type: ignore[call-arg]
