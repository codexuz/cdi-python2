#  bot/app/config.py
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    bot_ingest_token: str = Field(alias="BOT_INGEST_TOKEN")
    backend_base_url: str = Field(alias="BACKEND_BASE_URL")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    health_host: str = Field(default="0.0.0.0", alias="HEALTH_HOST")
    health_port: int = Field(default=8081, alias="HEALTH_PORT")
    
    # Support for BOT_PORT environment variable (for Coolify)
    bot_port: int = Field(default=8081, alias="BOT_PORT")

    model_config = {
        "case_sensitive": False,
        # Remove env_file for containerized deployment - use environment variables directly
        # "env_file": ".env",
        # "env_file_encoding": "utf-8",
    }


settings = Settings()
