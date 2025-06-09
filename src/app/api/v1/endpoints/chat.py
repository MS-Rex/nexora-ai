from fastapi import APIRouter, Depends, HTTPException
from src.app.models.pydantic.chat import ChatRequest, ChatResponse, EnhancedChatResponse
from src.app.agents.nexora_service import nexora_service
from src.app.core.auth.api_auth import verify_api_key
from typing import Annotated

router = APIRouter()

@router.post("/chat", response_model=EnhancedChatResponse)
async def enhanced_chat_with_agent(
    request: ChatRequest, api_key: Annotated[str, Depends(verify_api_key)]
) -> EnhancedChatResponse:
    """
    Enhanced chat endpoint with Nexora Campus Copilot.

    This endpoint:
    - Authenticates the request using API key
    - Uses Nexora Campus Copilot to handle university and campus-related queries
    - Automatically selects appropriate tools (events, departments, both, or none)
    - Politely redirects non-university questions to campus topics
    - Returns comprehensive response for campus-related queries
    """
    try:
        # Process message through the orchestrator service
        result = await nexora_service.chat(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id
        )

        # Return enhanced structured response
        return EnhancedChatResponse(
            response=result["response"],
            agent_name="Nexora Campus Copilot",  # University-focused AI assistant
            intent="campus",  # Single agent handles all campus-related intents
            agent_used=result["agent_used"],
            success=result["success"],
            error=result.get("error"),
            session_id=request.session_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing enhanced chat request: {str(e)}"
        )
