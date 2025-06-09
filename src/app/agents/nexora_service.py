from pydantic_ai.usage import Usage
from pydantic_ai.messages import ModelMessage
from src.app.agents.orchestrator_agent import orchestrator_agent
from src.app.services.conversation_service import ConversationService
from src.app.core.database.connection import get_database_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import logging
import httpx
import time

logger = logging.getLogger(__name__)


class NexoraService:
    """Simplified Nexora Campus Copilot service using a single Orchestrator Agent.
    
    This replaces the complex multi-agent routing system with a single intelligent agent
    that can handle any query type by selecting appropriate tools.
    """

    def __init__(self):
        """Initialize the service with the orchestrator agent."""
        self.orchestrator = orchestrator_agent
        self.service_name = "Nexora Campus Copilot"

    async def chat(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        message_history: Optional[list[ModelMessage]] = None,
        usage: Optional[Usage] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Process any user message using the orchestrator agent with conversation history.
        
        The orchestrator will automatically:
        1. Analyze the query to determine what information is needed
        2. Select and use appropriate tools (events, departments, both, or none)
        3. Compose a comprehensive response
        4. Save conversation history to database
        
        No intent classification or agent routing needed!

        Args:
            message: User's message (any type: events, departments, multi-domain, general)
            user_id: Optional user ID for tracking
            session_id: Optional session ID for conversation tracking
            message_history: Previous conversation messages for context (will be retrieved from DB if not provided)
            usage: Usage tracking object
            http_client: HTTP client for API calls
            db_session: Database session for conversation history

        Returns:
            Dictionary containing response and metadata
        """
        # Create HTTP client if not provided
        if http_client is None:
            http_client = httpx.AsyncClient()
            should_close_client = True
        else:
            should_close_client = False

        # Initialize usage tracking if not provided
        if usage is None:
            usage = Usage()

        # Generate session_id if not provided
        if session_id is None:
            from uuid import uuid4
            session_id = str(uuid4())

        start_time = time.time()
        
        try:
            # Get or create database session for conversation history
            if db_session is None:
                async for session in get_database_session():
                    conversation_service = ConversationService(session)
                    return await self._process_with_history(
                        conversation_service, message, user_id, session_id,
                        message_history, usage, http_client, start_time
                    )
            else:
                conversation_service = ConversationService(db_session)
                return await self._process_with_history(
                    conversation_service, message, user_id, session_id,
                    message_history, usage, http_client, start_time
                )

        except Exception as e:
            logger.error(f"Nexora service error for user {user_id}: {str(e)}")
            
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again later.",
                "agent_used": "Nexora Campus Copilot",
                "service": self.service_name,
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "session_id": session_id,
                "usage": usage.dict() if hasattr(usage, 'dict') else str(usage)
            }
        
        finally:
            # Close the client if we created it
            if should_close_client:
                await http_client.aclose()

    async def _process_with_history(
        self,
        conversation_service: ConversationService,
        message: str,
        user_id: Optional[str],
        session_id: str,
        message_history: Optional[list[ModelMessage]],
        usage: Usage,
        http_client: httpx.AsyncClient,
        start_time: float
    ) -> Dict[str, Any]:
        """Process message with conversation history management."""
        
        try:
            # Get or create conversation
            conversation = await conversation_service.get_or_create_conversation(
                session_id=session_id,
                user_id=user_id
            )

            # Get conversation history BEFORE saving current message (if not provided)
            if message_history is None:
                message_history = await conversation_service.get_conversation_history(
                    session_id=session_id,
                    limit=20  # Limit to last 20 messages for context
                )

            # Log conversation context for debugging
            logger.info(f"Session {session_id}: Processing message with {len(message_history)} previous messages in context")
            
            # Save user message AFTER retrieving history
            await conversation_service.save_user_message(
                conversation_id=conversation.id,
                content=message
            )

            # Let the orchestrator handle everything
            response = await self.orchestrator.handle_query(
                message=message,
                user_id=user_id,
                message_history=message_history,
                usage=usage,
                http_client=http_client
            )

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Save assistant response
            await conversation_service.save_assistant_message(
                conversation_id=conversation.id,
                content=response,
                agent_name="Nexora Campus Copilot",
                agent_used="Nexora Campus Copilot",
                intent="campus",
                success=True,
                usage_data=usage.dict() if hasattr(usage, 'dict') else {"usage": str(usage)},
                response_time_ms=response_time_ms
            )

            return {
                "response": response,
                "agent_used": "Nexora Campus Copilot",
                "service": self.service_name,
                "success": True,
                "user_id": user_id,
                "session_id": session_id,
                "conversation_id": conversation.id,
                "usage": usage.dict() if hasattr(usage, 'dict') else str(usage),
                "response_time_ms": response_time_ms
            }

        except Exception as e:
            logger.error(f"Error processing message with history: {str(e)}")
            
            # Try to save error message if we have conversation
            try:
                response_time_ms = int((time.time() - start_time) * 1000)
                error_response = "I apologize, but I'm experiencing technical difficulties. Please try again later."
                
                await conversation_service.save_assistant_message(
                    conversation_id=conversation.id,
                    content=error_response,
                    agent_name="Nexora Campus Copilot",
                    agent_used="Nexora Campus Copilot",
                    intent="error",
                    success=False,
                    error_message=str(e),
                    response_time_ms=response_time_ms
                )
            except:
                pass  # Don't let saving error fail the response
            
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again later.",
                "agent_used": "Nexora Campus Copilot",
                "service": self.service_name,
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "session_id": session_id,
                "usage": usage.dict() if hasattr(usage, 'dict') else str(usage)
            }

    async def get_service_info(self) -> Dict[str, Any]:
        """Get information about the service capabilities."""
        return {
            "service_name": self.service_name,
            "agent": "Nexora Campus Copilot",
            "capabilities": [
                "Campus events information",
                "Department information", 
                "Multi-domain campus queries",
                "University-related questions only",
                "Intelligent tool selection",
                "Real-time date and time information"
            ],
            "available_tools": [
                "fetch_events",
                "search_events", 
                "fetch_departments",
                "search_departments",
                "get_current_datetime",
                "get_date_info",
                "get_time_info"
            ],
            "architecture": "Single Campus Copilot Agent with intelligent tool selection"
        }


# Global service instance
nexora_service = NexoraService() 