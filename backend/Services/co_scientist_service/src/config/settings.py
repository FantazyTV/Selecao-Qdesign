from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CO_SCIENTIST_", env_file=ENV_FILE, extra="ignore"
    )

    service_name: str = "co_scientist_service"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    openrouter_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "CO_SCIENTIST_OPENROUTER_API_KEY", "OPENROUTER_API_KEY"
        ),
    )
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = Field(
        default="gryphe/mythomuse-7b:free",
        validation_alias=AliasChoices(
            "CO_SCIENTIST_OPENROUTER_MODEL", "OPENROUTER_MODEL"
        ),
    )
    openrouter_timeout: int = 30
    openrouter_http_referer: str | None = None
    openrouter_app_title: str | None = None
    openrouter_max_retries: int = 3


settings = Settings()
