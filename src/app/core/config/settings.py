import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service Configuration
    SERVICE_NAME: str = "nexora-ai"
    DEBUG: bool = True
    API_VERSION: str = "v1"

    # API Authentication
    API_KEY: str = "poc-key-123"

    # AI Model Configuration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


# Global settings instance
settings = Settings()
