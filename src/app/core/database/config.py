from typing import Optional
import os
from src.app.core.config.settings import settings


def get_database_url() -> str:
    """
    Construct PostgreSQL database URL from environment variables.

    Returns:
        PostgreSQL connection string
    """
    # Get database configuration from environment or use defaults
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "nexora_ai")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")

    # Construct PostgreSQL URL for asyncpg
    return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


# Database configuration settings
DATABASE_CONFIG = {
    "url": get_database_url(),
    "echo": os.getenv("DB_ECHO", "false").lower() == "true",  # SQL logging
    "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),  # 1 hour
}
