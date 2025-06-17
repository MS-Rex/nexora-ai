from fastapi import APIRouter, Depends, HTTPException
from src.app.models.pydantic.chat import ChatRequest, ChatResponse, EnhancedChatResponse
from src.app.agents.nexora_service import nexora_service
from src.app.core.auth.api_auth import verify_api_key
from src.app.core.database.connection import get_database_session
from src.app.services.moderation_service import moderation_service
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=EnhancedChatResponse)
async def enhanced_chat_with_agent(
    request: ChatRequest,
    api_key: Annotated[str, Depends(verify_api_key)],
    db_session: AsyncSession = Depends(get_database_session),
) -> EnhancedChatResponse:
    """
    Enhanced chat endpoint with Nexora Campus Copilot.

    This endpoint:
    - Authenticates the request using API key
    - Performs content moderation to filter inappropriate messages
    - Uses Nexora Campus Copilot to handle university and campus-related queries
    - Automatically selects appropriate tools (events, departments, both, or none)
    - Politely redirects non-university questions to campus topics
    - Returns comprehensive response for campus-related queries
    """
    try:
        # Step 1: Content Moderation - Check BEFORE processing with LLM
        logger.info(f"Moderating content for user {request.user_id}")
        moderation_result = await moderation_service.moderate_content(request.message)
        
        # If content is flagged, return moderation response WITHOUT calling LLM
        if moderation_result.flagged:
            logger.warning(
                f"Content flagged for user {request.user_id}: {moderation_result.reason}"
            )
            
            # Generate appropriate moderation response
            moderation_response = moderation_service.get_moderation_response_message(
                moderation_result
            )
            
            return EnhancedChatResponse(
                response=moderation_response,
                agent_name="Nexora Campus Copilot",
                intent="moderation",  # Special intent for moderated content
                agent_used="Content Moderation",
                success=True,  # Request was handled successfully (by blocking it)
                error=None,
                session_id=request.session_id,
                moderated=True,
                content_flagged=True,
                moderation_reason=moderation_result.reason,
            )

        # Step 2: Content passed moderation - process normally
        logger.info(f"Content passed moderation for user {request.user_id}")
        
        # Process message through the orchestrator service with conversation history
        result = await nexora_service.chat(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            db_session=db_session,
        )

        # Return enhanced structured response with moderation metadata
        return EnhancedChatResponse(
            response=result["response"],
            agent_name="Nexora Campus Copilot",  # University-focused AI assistant
            intent="campus",  # Single agent handles all campus-related intents
            agent_used=result["agent_used"],
            success=result["success"],
            error=result.get("error"),
            session_id=request.session_id,
            moderated=True,
            content_flagged=False,
            moderation_reason=None,
        )

    except Exception as e:
        logger.error(f"Error processing enhanced chat request: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing enhanced chat request: {str(e)}"
        )
