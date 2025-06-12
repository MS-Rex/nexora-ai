from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
import logging
import os
from .config import DATABASE_CONFIG

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self):
        self._engine = None
        self._session_factory = None

    def initialize(self):
        """Initialize the database engine and session factory."""
        try:
            # Use different configurations based on environment
            engine_kwargs = {
                "url": DATABASE_CONFIG["url"],
                "echo": DATABASE_CONFIG["echo"],
            }

            # For development, use NullPool (no connection pooling)
            # For production, you might want to use the default pool with proper settings
            use_null_pool = os.getenv("DB_USE_NULL_POOL", "true").lower() == "true"

            if use_null_pool:
                # NullPool doesn't support pool arguments
                engine_kwargs["poolclass"] = NullPool
            else:
                # Use connection pooling with proper arguments
                engine_kwargs.update(
                    {
                        "pool_size": DATABASE_CONFIG["pool_size"],
                        "max_overflow": DATABASE_CONFIG["max_overflow"],
                        "pool_timeout": DATABASE_CONFIG["pool_timeout"],
                        "pool_recycle": DATABASE_CONFIG["pool_recycle"],
                    }
                )

            self._engine = create_async_engine(**engine_kwargs)

            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            logger.info("Database engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session.

        Yields:
            AsyncSession: Database session
        """
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        async with self._session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()

    async def close(self):
        """Close the database engine."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database engine closed")


# Global database manager instance
db_manager = DatabaseManager()


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session for FastAPI.

    Yields:
        AsyncSession: Database session
    """
    async for session in db_manager.get_session():
        yield session
