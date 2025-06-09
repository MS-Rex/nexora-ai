from pydantic_ai.usage import Usage
from pydantic_ai.messages import ModelMessage
from src.app.agents.orchestrator_agent import orchestrator_agent
from typing import Optional, Dict, Any
import logging
import httpx

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
        http_client: Optional[httpx.AsyncClient] = None
    ) -> Dict[str, Any]:
        """
        Process any user message using the orchestrator agent.
        
        The orchestrator will automatically:
        1. Analyze the query to determine what information is needed
        2. Select and use appropriate tools (events, departments, both, or none)
        3. Compose a comprehensive response
        
        No intent classification or agent routing needed!

        Args:
            message: User's message (any type: events, departments, multi-domain, general)
            user_id: Optional user ID for tracking
            session_id: Optional session ID for conversation tracking
            message_history: Previous conversation messages for context
            usage: Usage tracking object
            http_client: HTTP client for API calls

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

        try:
            # Let the orchestrator handle everything
            response = await self.orchestrator.handle_query(
                message=message,
                user_id=user_id,
                message_history=message_history,
                usage=usage,
                http_client=http_client
            )

            return {
                "response": response,
                "agent_used": "Nexora Campus Copilot",
                "service": self.service_name,
                "success": True,
                "user_id": user_id,
                "session_id": session_id,
                "usage": usage.dict() if hasattr(usage, 'dict') else str(usage)
            }

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
                "Intelligent tool selection"
            ],
            "available_tools": [
                "fetch_events",
                "search_events", 
                "fetch_departments",
                "search_departments"
            ],
            "architecture": "Single Campus Copilot Agent with intelligent tool selection"
        }


# Global service instance
nexora_service = NexoraService() 