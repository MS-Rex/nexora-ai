"""
Pydantic models for chat functionality.

This module contains data models for chat requests, responses, and related functionality.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint from Laravel."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User message to send to the agent",
    )
    user_id: Optional[str] = Field(None, description="User ID from Laravel (optional)")
    session_id: Optional[str] = Field(
        None, description="Session ID for conversation tracking (optional)"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint to Laravel."""

    response: str = Field(..., description="Agent's response message")
    agent_name: str = Field(..., description="Name of the agent that responded")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    session_id: Optional[str] = Field(None, description="Session ID if provided")


class EnhancedChatResponse(BaseModel):
    """Enhanced response model with multi-agent metadata."""

    response: str = Field(..., description="Agent's response message")
    agent_name: str = Field(..., description="Name of the agent that responded")
    intent: str = Field(..., description="Classified intent category")
    agent_used: str = Field(
        ..., description="Display name of the specialized agent used"
    )
    success: bool = Field(
        ..., description="Whether the request was processed successfully"
    )
    error: Optional[str] = Field(None, description="Error message if processing failed")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    session_id: Optional[str] = Field(None, description="Session ID if provided")
    # Moderation fields
    moderated: bool = Field(
        default=False, description="Whether content was checked by moderation"
    )
    content_flagged: bool = Field(
        default=False,
        description="Whether the input content was flagged as inappropriate",
    )
    moderation_reason: Optional[str] = Field(
        None, description="Reason for content flagging if applicable"
    )
