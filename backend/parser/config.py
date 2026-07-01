import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Stage 1 & 2 Config
    DIGITAL_PDF_THRESHOLD: int = 100
    OCR_PROVIDER: str = "tesseract"
    CONFIDENCE_THRESHOLD: float = 0.8
    MAX_RETRIES: int = 3

    # Stage 4 Config
    DIAL_API_KEY: str = ""
    DIAL_MODEL: str = "gpt-4o-mini"
    OLLAMA_MODEL: str = "llama3.2"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Stage 6 Config
    DATABASE_URL: str = "sqlite+aiosqlite:///parser/parser_resumes.db"

    # Automatically load values from the .env file in backend/
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Expose settings instance
settings = Settings()

# Expose constants so all other modules can import them unchanged
DIGITAL_PDF_THRESHOLD = settings.DIGITAL_PDF_THRESHOLD
OCR_PROVIDER = settings.OCR_PROVIDER
CONFIDENCE_THRESHOLD = settings.CONFIDENCE_THRESHOLD
MAX_RETRIES = settings.MAX_RETRIES
DIAL_API_KEY = settings.DIAL_API_KEY
DIAL_MODEL = settings.DIAL_MODEL
OLLAMA_MODEL = settings.OLLAMA_MODEL
GEMINI_API_KEY = settings.GEMINI_API_KEY
GEMINI_MODEL = settings.GEMINI_MODEL
DATABASE_URL = settings.DATABASE_URL
