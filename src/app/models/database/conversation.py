from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Integer,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4
from .base import Base


class Conversation(Base):
    """
    Represents a conversation session between a user and the AI agent.
    Each conversation can contain multiple messages.
    """

    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)  # Optional, from Laravel
    title = Column(
        String(255), nullable=True
    )  # Can be auto-generated from first message
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active = Column(Boolean, default=True)

    # Metadata
    total_messages = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to messages
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    """
    Represents a single message in a conversation.
    Can be from user or AI agent.
    """

    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    conversation_id = Column(
        String, ForeignKey("conversations.id"), nullable=False, index=True
    )

    # Message content
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # AI Agent metadata (only for assistant messages)
    agent_name = Column(String(100), nullable=True)
    agent_used = Column(String(100), nullable=True)
    intent = Column(String(100), nullable=True)
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)

    # Usage and performance metadata
    usage_data = Column(JSON, nullable=True)  # Store pydantic_ai usage data
    response_time_ms = Column(Integer, nullable=True)

    # Relationship back to conversation
    conversation = relationship("Conversation", back_populates="messages")

    def to_model_message(self):
        """Convert to pydantic_ai ModelMessage format for agent context."""
        from pydantic_ai.messages import (
            ModelRequest,
            ModelResponse,
            UserPromptPart,
            TextPart,
        )

        if self.role == "user":
            return ModelRequest(parts=[UserPromptPart(content=self.content)])
        else:
            return ModelResponse(parts=[TextPart(content=self.content)])
