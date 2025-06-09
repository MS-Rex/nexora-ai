from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.app.api.v1.endpoints import chat, health
from src.app.core.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    print(f"🚀 {settings.SERVICE_NAME} starting up...")
    print(f"📡 API available at /api/{settings.API_VERSION}")
    print(f"📖 Documentation at /docs")

    yield

    # Shutdown
    print(f"🛑 {settings.SERVICE_NAME} shutting down...")


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
