from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    gemini_api_key: str
    gemini_model: str = "gemini-3.1-flash-lite"

    playwright_workspace: str = "../playwright-workspace"

    playwright_workspace_path: str
    
    playwright_timeout_ms: int = 120000 

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
