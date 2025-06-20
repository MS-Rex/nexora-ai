import os
from functools import lru_cache
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
    BASE_URL: str = (
        "https://nexora.msanjana.com/api"  # Default fallback if not set in .env
    )

    # API Authentication
    API_KEY: str = "poc-key-123"

    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "nexora_ai"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    # AI Model Configuration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # RAG Configuration
    KNOWLEDGE_BASE_PATH: str = "./knowledge_base"
    VECTOR_DB_PATH: str = "./storage/vector_db"
    RAG_TABLE_NAME: str = "nexora_knowledge"
    RAG_CHUNK_SIZE: int = 8192
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    RAG_MAX_RESULTS: int = 10
    EMBEDDING_MODEL: str = "text-embedding-3-large"

    # Logging
    LOGFIRE_TOKEN: Optional[str] = None
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_openai()
logfire.info("APP STARTED, {place}!", place="Nexora AI")
