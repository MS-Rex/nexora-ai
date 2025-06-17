from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.app.api.v1.endpoints import chat, health, conversations, voice, moderation
from src.app.core.config.settings import settings
from src.app.core.database.connection import db_manager
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    print(f"🚀 {settings.SERVICE_NAME} starting up...")
    print(f"📡 API available at /api/{settings.API_VERSION}")
    print(f"📖 Documentation at /docs")

    # Initialize database
    try:
        db_manager.initialize()
        print("✅ Database connection initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        # You may want to raise this error to prevent startup if DB is critical
        # raise

    yield

    # Shutdown
    print(f"🛑 {settings.SERVICE_NAME} shutting down...")

    # Close database connections
    try:
        await db_manager.close()
        print("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database connections: {e}")


# Create FastAPI app
app = FastAPI(
    title=f"{settings.SERVICE_NAME} API",
    description="PydanticAI-powered microservice for Laravel integration",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Add CORS middleware for Laravel integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix=f"/api/{settings.API_VERSION}", tags=["Chat"])

app.include_router(
    health.router, prefix=f"/api/{settings.API_VERSION}", tags=["Health"]
)

app.include_router(
    conversations.router, prefix=f"/api/{settings.API_VERSION}", tags=["Conversations"]
)

app.include_router(voice.router, prefix=f"/api/{settings.API_VERSION}", tags=["Voice"])

app.include_router(
    moderation.router, prefix=f"/api/{settings.API_VERSION}", tags=["Moderation"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.SERVICE_NAME,
        "status": "running",
        "api_version": settings.API_VERSION,
        "docs": "/docs",
    }
