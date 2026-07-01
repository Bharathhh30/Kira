from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "Kira API"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://kira:kira_password@localhost:5432/kira"
    )

    # Security
    JWT_SECRET_KEY: str = Field(
        default="super_secret_jwt_access_key_change_me_in_production"
    )
    JWT_REFRESH_SECRET_KEY: str = Field(
        default="super_secret_jwt_refresh_key_change_me_in_production"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = False

    # Google Gemini API
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")


settings = Settings()
