from fastapi import APIRouter, Depends, HTTPException
from src.app.schemas.chat import ChatRequest, ChatResponse
from src.app.agents.chat_agent import chat_agent_service
from src.app.core.auth.api_auth import verify_api_key
from typing import Annotated

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest, api_key: Annotated[str, Depends(verify_api_key)]
) -> ChatResponse:
    """
    Chat endpoint for Laravel to send messages to the PydanticAI agent.

    This endpoint:
    - Authenticates the request using API key
    - Sends the message to the PydanticAI agent
    - Returns the agent's response in a structured format
    """
    try:
        # Send message to the agent
        agent_response = await chat_agent_service.chat(
            message=request.message, user_id=request.user_id
        )

        # Return structured response
        return ChatResponse(
            response=agent_response,
            agent_name=chat_agent_service.agent_name,
            session_id=request.session_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing chat request: {str(e)}"
        )
