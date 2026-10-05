from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Job Hunter API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://jobhunter:jobhunter@db:5432/jobhunter"
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)
    cors_origins: str = "http://localhost:3100"
    llm_api_key: str | None = None
    llm_base_url: str = "https://llm.4geeks.ai"
    llm_model: str = "madrid-spain/opnerouter/openai/gpt-6-luna"
    llm_timeout_seconds: float = Field(default=60.0, ge=1.0, le=60.0)
    enable_eures_connector: bool = False
    enable_deterministic_demo_matching: bool = False
    adzuna_app_id: str | None = None
    adzuna_app_key: str | None = None
    require_invite: bool = False
    registration_allowlist: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_registration_emails(self) -> set[str]:
        return {
            email.strip().lower()
            for email in self.registration_allowlist.split(",")
            if email.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
