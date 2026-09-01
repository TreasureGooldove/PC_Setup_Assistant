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
    llm_timeout_seconds: float = Field(default=20.0, ge=5.0, le=60.0)
    llm_max_output_tokens: int = Field(default=1400, ge=300, le=4000)
    steam_api_enabled: bool = False
    steam_api_base: str = "https://store.steampowered.com/api"
    realtime_prices_required: bool = False
    taobao_mcp_enabled: bool = False
    taobao_mcp_command: str = "python"
    taobao_mcp_server_path: str = ""
    taobao_mcp_working_directory: str | None = None
    taobao_mcp_fetch_tool: str = "taobao_fetch_product"
    taobao_product_urls_json: str = "{}"
    # 可选 ModelScope/open-webSearch MCP：默认关闭，开启后只用于公开社区搜索摘要。
    modelscope_mcp_enabled: bool = False
    modelscope_mcp_command: str = "npx"
    modelscope_mcp_args_json: str = '["-y", "open-websearch@2.1.9"]'
    modelscope_mcp_env_json: str = '{"MODE":"stdio","ALLOWED_SEARCH_ENGINES":"baidu,bing"}'
    modelscope_mcp_working_directory: str | None = None
    modelscope_mcp_timeout_seconds: float = Field(default=18.0, ge=5.0, le=60.0)
    community_search_max_results: int = Field(default=5, ge=1, le=8)
    jd_public_fetch_enabled: bool = False
    jd_product_urls_json: str = "{}"
    # 只对明确绑定的 detail.zol.com.cn 参数页启用；页面报价仍按公开参考价处理。
    zol_public_fetch_enabled: bool = True
    zol_product_urls_json: str = "{}"
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

    @property
    def zol_product_urls(self) -> dict[str, str]:
        try:
            payload = json.loads(self.zol_product_urls_json)
        except json.JSONDecodeError:
            return {}
        if not isinstance(payload, dict):
            return {}
        return {str(key): str(value) for key, value in payload.items() if str(value).strip()}

    @property
    def taobao_product_urls(self) -> dict[str, str]:
        try:
            payload = json.loads(self.taobao_product_urls_json)
        except json.JSONDecodeError:
            return {}
        if not isinstance(payload, dict):
            return {}
        return {str(key): str(value) for key, value in payload.items() if str(value).strip()}

    @property
    def modelscope_mcp_env(self) -> dict[str, str]:
        """返回不包含认证信息的 MCP 进程环境覆盖项。"""

        result: dict[str, str] = {
            "MODE": "stdio",
            "ALLOWED_SEARCH_ENGINES": "baidu,bing",
        }
        try:
            payload = json.loads(self.modelscope_mcp_env_json)
        except json.JSONDecodeError:
            return result
        if not isinstance(payload, dict):
            return result
        blocked = ("key", "token", "secret", "cookie", "password", "auth")
        for key, value in list(payload.items())[:16]:
            name = str(key).strip()
            if (
                not name
                or len(name) > 80
                or any(word in name.lower() for word in blocked)
                or not isinstance(value, (str, int, float, bool))
            ):
                continue
            text = str(value)
            if name == "MODE" and text != "stdio":
                continue
            if len(text) <= 300:
                result[name] = text
        result["MODE"] = "stdio"
        return result


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
