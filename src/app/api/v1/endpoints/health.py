from fastapi import APIRouter
from src.app.schemas.chat import HealthResponse
from src.app.core.config.settings import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for Laravel to monitor service status.

    This endpoint:
    - Returns service health status
    - Can be called without authentication
    - Used for monitoring and load balancing
    """
    return HealthResponse(
        status="healthy", service=settings.SERVICE_NAME, version="1.0.0"
    )
