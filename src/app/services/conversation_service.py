from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from src.app.models.database.conversation import Conversation, Message
from pydantic_ai.messages import ModelMessage
from typing import Optional, List, Dict, Any
from uuid import uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversation history in the database."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_or_create_conversation(
        self, session_id: str, user_id: Optional[str] = None
    ) -> Conversation:
        """
        Get existing conversation by session_id or create a new one.

        Args:
            session_id: Session identifier
            user_id: Optional user identifier

        Returns:
            Conversation object
        """
        try:
            # Try to find existing conversation
            result = await self.db.execute(
                select(Conversation).where(Conversation.session_id == session_id)
            )
            conversation = result.scalar_one_or_none()

            if conversation:
                # Update last activity
                conversation.last_activity = datetime.utcnow()
                await self.db.commit()
                return conversation

            # Create new conversation
            conversation = Conversation(
                session_id=session_id,
                user_id=user_id,
                title=None,  # Will be set based on first message
            )

            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)

            logger.info(f"Created new conversation: {conversation.id}")
            return conversation

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating/retrieving conversation: {e}")
            raise

    async def save_user_message(self, conversation_id: str, content: str) -> Message:
        """
        Save user message to the database.

        Args:
            conversation_id: ID of the conversation
            content: Message content

        Returns:
            Message object
        """
        try:
            message = Message(
                conversation_id=conversation_id, content=content, role="user"
            )

            self.db.add(message)
            await self._update_conversation_metadata(conversation_id, content)
            await self.db.commit()
            await self.db.refresh(message)

            return message

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error saving user message: {e}")
            raise

    async def save_assistant_message(
        self,
        conversation_id: str,
        content: str,
        agent_name: str,
        agent_used: str,
        intent: str,
        success: bool,
        usage_data: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Message:
        """
        Save assistant message to the database.

        Args:
            conversation_id: ID of the conversation
            content: Message content
            agent_name: Name of the agent
            agent_used: Agent that was used
            intent: Classified intent
            success: Whether the request was successful
            usage_data: Usage tracking data
            response_time_ms: Response time in milliseconds
            error_message: Error message if any

        Returns:
            Message object
        """
        try:
            message = Message(
                conversation_id=conversation_id,
                content=content,
                role="assistant",
                agent_name=agent_name,
                agent_used=agent_used,
                intent=intent,
                success=success,
                usage_data=usage_data,
                response_time_ms=response_time_ms,
                error_message=error_message,
            )

            self.db.add(message)
            await self._update_conversation_metadata(conversation_id)
            await self.db.commit()
            await self.db.refresh(message)

            return message

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error saving assistant message: {e}")
            raise

    async def get_conversation_history(
        self, session_id: str, limit: int = 50
    ) -> List[ModelMessage]:
        """
        Get conversation history formatted for pydantic_ai.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve

        Returns:
            List of ModelMessage objects for agent context
        """
        try:
            # Get conversation with messages
            result = await self.db.execute(
                select(Conversation)
                .options(selectinload(Conversation.messages))
                .where(Conversation.session_id == session_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                return []

            # Get recent messages, ordered by creation time
            result = await self.db.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(desc(Message.created_at))
                .limit(limit)
            )
            messages = result.scalars().all()

            # Convert to ModelMessage format and reverse to get chronological order
            model_messages = []
            for message in reversed(messages):
                model_messages.append(message.to_model_message())

            return model_messages

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []

    async def get_conversation_summary(
        self, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation summary with metadata.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with conversation summary
        """
        try:
            result = await self.db.execute(
                select(Conversation).where(Conversation.session_id == session_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                return None

            return {
                "conversation_id": conversation.id,
                "session_id": conversation.session_id,
                "user_id": conversation.user_id,
                "title": conversation.title,
                "total_messages": conversation.total_messages,
                "created_at": conversation.created_at,
                "last_activity": conversation.last_activity,
                "is_active": conversation.is_active,
            }

        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return None

    async def _update_conversation_metadata(
        self, conversation_id: str, first_message_content: Optional[str] = None
    ):
        """
        Update conversation metadata (message count, title, last activity).

        Args:
            conversation_id: ID of the conversation
            first_message_content: Content of first message to generate title
        """
        try:
            # Get conversation
            result = await self.db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one()

            # Update message count
            result = await self.db.execute(
                select(func.count(Message.id)).where(
                    Message.conversation_id == conversation_id
                )
            )
            total_messages = result.scalar()

            conversation.total_messages = total_messages
            conversation.last_activity = datetime.utcnow()

            # Set title from first message if not set
            if not conversation.title and first_message_content:
                # Generate a simple title from first 50 characters
                title = first_message_content[:50].strip()
                if len(first_message_content) > 50:
                    title += "..."
                conversation.title = title

        except Exception as e:
            logger.error(f"Error updating conversation metadata: {e}")
            raise

    async def deactivate_conversation(self, session_id: str) -> bool:
        """
        Deactivate a conversation (soft delete).

        Args:
            session_id: Session identifier

        Returns:
            True if conversation was deactivated, False if not found
        """
        try:
            result = await self.db.execute(
                select(Conversation).where(Conversation.session_id == session_id)
            )
            conversation = result.scalar_one_or_none()

            if conversation:
                conversation.is_active = False
                await self.db.commit()
                return True

            return False

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deactivating conversation: {e}")
            raise
