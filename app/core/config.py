from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    bot_token: SecretStr = Field(default=SecretStr(""))
    bot_mode: Literal["polling", "webhook"] = "polling"
    webhook_base_url: str = ""
    webhook_path: str = "/telegram/webhook"
    webhook_secret: SecretStr = Field(default=SecretStr("change-this-secret"))
    template_webapp_url: str = ""

    database_url: str = "postgresql+asyncpg://cvbot:cvbot@localhost:5432/cvbot"
    redis_url: str = "redis://localhost:6379/0"
    storage_dir: Path = Path("storage")

    gemini_api_key: SecretStr = Field(default=SecretStr(""))
    gemini_model: str = "gemini-3.6-flash"
    gemini_router_model: str = "gemini-3.5-flash-lite"
    gemini_voice_model: str = "gemini-3.5-transcribe"

    @property
    def webhook_url(self) -> str:
        return f"{self.webhook_base_url.rstrip('/')}{self.webhook_path}"

    def ensure_valid_runtime(self) -> None:
        token = self.bot_token.get_secret_value()
        if not token or "REPLACE_WITH" in token:
            raise RuntimeError("BOT_TOKEN is required. Copy .env.example to .env and set it.")
        if self.bot_mode == "webhook" and not self.webhook_base_url.startswith("https://"):
            raise RuntimeError("WEBHOOK_BASE_URL must be an HTTPS URL in webhook mode.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
