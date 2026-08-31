import json
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./data/assistant.db"
    llm_enabled: bool = False
    llm_api_key: str | None = None
    llm_api_base: str = "https://example.invalid/compatible-mode/v1"
    llm_model: str = "qwen3.8-max"
    steam_api_enabled: bool = False
    steam_api_base: str = "https://store.steampowered.com/api"
    jd_public_fetch_enabled: bool = False
    jd_product_urls_json: str = "{}"
    catalog_public_sync_enabled: bool = True
    catalog_sync_ttl_hours: int = Field(default=12, ge=1, le=168)
    catalog_sync_max_items: int = Field(default=40, ge=5, le=48)
    catalog_sync_timeout_seconds: float = Field(default=8.0, ge=2.0, le=30.0)
    catalog_sync_max_response_bytes: int = Field(default=1_000_000, ge=100_000, le=2_000_000)
    cors_origins: str = "http://localhost:5173"
    job_lease_seconds: int = Field(default=60, ge=10, le=3600)
    job_poll_seconds: float = Field(default=0.5, ge=0.1, le=30)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def jd_product_urls(self) -> dict[str, str]:
        try:
            payload = json.loads(self.jd_product_urls_json)
        except json.JSONDecodeError:
            return {}
        if not isinstance(payload, dict):
            return {}
        return {str(key): str(value) for key, value in payload.items()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
