import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import logfire


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service Configuration
    SERVICE_NAME: str = "nexora-ai"
    DEBUG: bool = True
    API_VERSION: str = "v1"

    # API Configuration
    BASE_URL: str = "http://localhost:8000/api"  # Default fallback if not set in .env
    
    # API Authentication
    API_KEY: str = "poc-key-123"

    # AI Model Configuration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Logging
    LOGFIRE_TOKEN: Optional[str] = None
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


# Global settings instance
settings = Settings()
logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_openai()
logfire.info('APP STARTED, {place}!', place='Nexora AI')
