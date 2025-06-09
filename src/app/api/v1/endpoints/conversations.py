from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.core.database.connection import get_database_session
from src.app.services.conversation_service import ConversationService
from src.app.core.auth.api_auth import verify_api_key
from typing import Annotated, Optional, List, Dict, Any
from pydantic import BaseModel

router = APIRouter()


class ConversationSummaryResponse(BaseModel):
    """Response model for conversation summary."""
    conversation_id: str
    session_id: str
    user_id: Optional[str]
    title: Optional[str]
    total_messages: int
    created_at: str
    last_activity: str
    is_active: bool


class MessageResponse(BaseModel):
    """Response model for a single message."""
    id: str
    role: str
    content: str
    created_at: str
    agent_name: Optional[str] = None
    agent_used: Optional[str] = None
    intent: Optional[str] = None
    success: Optional[bool] = None
    response_time_ms: Optional[int] = None


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history."""
    conversation: ConversationSummaryResponse
    messages: List[MessageResponse]


@router.get("/conversations/{session_id}/summary", response_model=ConversationSummaryResponse)
async def get_conversation_summary(
    session_id: str,
    api_key: Annotated[str, Depends(verify_api_key)],
    db_session: AsyncSession = Depends(get_database_session)
) -> ConversationSummaryResponse:
    """
    Get conversation summary by session ID.
    
    Args:
        session_id: Session identifier
        api_key: API key for authentication
        db_session: Database session
        
    Returns:
        Conversation summary with metadata
    """
    try:
        conversation_service = ConversationService(db_session)
        summary = await conversation_service.get_conversation_summary(session_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return ConversationSummaryResponse(
            conversation_id=summary["conversation_id"],
            session_id=summary["session_id"],
            user_id=summary["user_id"],
            title=summary["title"],
            total_messages=summary["total_messages"],
            created_at=summary["created_at"].isoformat(),
            last_activity=summary["last_activity"].isoformat(),
            is_active=summary["is_active"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving conversation summary: {str(e)}"
        )


@router.get("/conversations/{session_id}/history", response_model=List[MessageResponse])
async def get_conversation_history(
    session_id: str,
    api_key: Annotated[str, Depends(verify_api_key)],
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of messages to retrieve"),
    db_session: AsyncSession = Depends(get_database_session)
) -> List[MessageResponse]:
    """
    Get conversation message history by session ID.
    
    Args:
        session_id: Session identifier
        api_key: API key for authentication
        limit: Maximum number of messages to retrieve
        db_session: Database session
        
    Returns:
        List of messages in chronological order
    """
    try:
        conversation_service = ConversationService(db_session)
        
        # Get conversation to verify it exists
        summary = await conversation_service.get_conversation_summary(session_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages using database query instead of ModelMessage format
        from sqlalchemy import select, desc
        from src.app.models.database.conversation import Conversation, Message
        
        # Get conversation
        result = await db_session.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages
        result = await db_session.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at)  # Chronological order
            .limit(limit)
        )
        messages = result.scalars().all()
        
        # Convert to response format
        message_responses = []
        for message in messages:
            message_responses.append(MessageResponse(
                id=message.id,
                role=message.role,
                content=message.content,
                created_at=message.created_at.isoformat(),
                agent_name=message.agent_name,
                agent_used=message.agent_used,
                intent=message.intent,
                success=message.success,
                response_time_ms=message.response_time_ms
            ))
        
        return message_responses
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving conversation history: {str(e)}"
        )


@router.delete("/conversations/{session_id}")
async def deactivate_conversation(
    session_id: str,
    api_key: Annotated[str, Depends(verify_api_key)],
    db_session: AsyncSession = Depends(get_database_session)
) -> Dict[str, str]:
    """
    Deactivate a conversation (soft delete).
    
    Args:
        session_id: Session identifier
        api_key: API key for authentication
        db_session: Database session
        
    Returns:
        Success message
    """
    try:
        conversation_service = ConversationService(db_session)
        success = await conversation_service.deactivate_conversation(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": f"Conversation {session_id} deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error deactivating conversation: {str(e)}"
        ) 