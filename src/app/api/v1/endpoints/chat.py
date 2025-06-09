from fastapi import APIRouter, Depends, HTTPException
from src.app.schemas.chat import ChatRequest, ChatResponse, EnhancedChatResponse
from src.app.agents.chat_agent import chat_agent_service
from src.app.core.auth.api_auth import verify_api_key
from typing import Annotated

router = APIRouter()

@router.post("/chat", response_model=EnhancedChatResponse)
async def enhanced_chat_with_agent(
    request: ChatRequest, api_key: Annotated[str, Depends(verify_api_key)]
) -> EnhancedChatResponse:
    """
    Enhanced chat endpoint with multi-agent routing and intent classification.

    This endpoint:
    - Authenticates the request using API key
    - Classifies user intent and routes to appropriate specialized agent
    - Returns enhanced response with agent metadata and intent information
    """
    try:
        # Process message through multi-agent router
        result = await chat_agent_service.chat_with_routing(
            message=request.message, user_id=request.user_id
        )

        # Return enhanced structured response
        return EnhancedChatResponse(
            response=result["response"],
            agent_name="Nexora AI Assistant",  # Overall system name
            intent=result["intent"],
            agent_used=result["agent_used"],
            success=result["success"],
            error=result.get("error"),
            session_id=request.session_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing enhanced chat request: {str(e)}"
        )
