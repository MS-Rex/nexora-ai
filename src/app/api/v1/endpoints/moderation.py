from fastapi import APIRouter, Depends, HTTPException
from src.app.services.moderation_service import moderation_service, ModerationResult
from src.app.core.auth.api_auth import verify_api_key
from pydantic import BaseModel, Field
from typing import Annotated
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ModerationRequest(BaseModel):
    """Request model for content moderation."""

    content: str = Field(
        ..., min_length=1, max_length=2000, description="Content to moderate"
    )


@router.post("/moderate", response_model=ModerationResult)
async def moderate_content(
    request: ModerationRequest,
    api_key: Annotated[str, Depends(verify_api_key)],
) -> ModerationResult:
    """
    Moderate content for policy violations.

    This endpoint allows testing the moderation functionality independently
    and can be used by other services that need content moderation.

    Returns detailed moderation results including:
    - Whether content is flagged
    - Specific categories of violations
    - Human-readable reason for flagging
    - Confidence score if available
    """
    try:
        logger.info("Processing moderation request")
        result = await moderation_service.moderate_content(request.content)

        if result.flagged:
            logger.warning(f"Content flagged: {result.reason}")
        else:
            logger.info("Content passed moderation")

        return result

    except Exception as e:
        logger.error(f"Error in moderation endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing moderation request: {str(e)}"
        )
