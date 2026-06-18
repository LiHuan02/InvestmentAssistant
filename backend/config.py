from functools import lru_cache
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import DotEnvSettingsSource, EnvSettingsSource


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8000

    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o-mini"
    ai_max_tokens: int = 2048
    ai_temperature: float = 0.7

    twelvedata_api: str = ""
    tavily_api_key: str = ""

    rag_persist_dir: str = ""

    market_refresh_interval: int = 60
    news_refresh_interval: int = 300

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: Any,
        env_settings: EnvSettingsSource,
        dotenv_settings: DotEnvSettingsSource,
        file_secret_settings: Any,
    ) -> tuple:
        return (init_settings, dotenv_settings, env_settings, file_secret_settings)


@lru_cache
def get_settings() -> Settings:
    return Settings()
