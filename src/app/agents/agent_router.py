from typing import Optional, Dict, Any
import logging
import httpx
from pydantic_ai.usage import Usage, UsageLimits
from pydantic_ai.messages import ModelMessage
from src.app.agents.intent_classifier_agent import intent_classifier_agent
from src.app.agents.events_agent import events_agent
from src.app.agents.chat_agent import chat_agent_service

logger = logging.getLogger(__name__)


class AgentRouter:
    """Central Router for Nexora Campus Copilot multi-agent system.
    
    Implements the scalable agentic architecture methodology where the Router Agent 
    (Intention Classifier) serves as the main entry point for user queries and 
    dispatches requests to appropriate specialized agents.
    """
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.cleanup()

    def __init__(self):
        """Initialize the agent router with available specialized agents per Nexora Campus Copilot methodology."""
        self.intent_classifier = intent_classifier_agent  # Router Agent (Intention Classifier)
        
        # Currently implemented specialized agents
        self.agents = {
            "events": events_agent,           # Events Agent - campus events, schedules, reminders
            "general": chat_agent_service,    # General chat agent for other queries
        }
        
        # TODO: Future agents:
        # "schedule": Schedule Agent - personal or general class schedules  
        # "cafeteria": Cafeteria Agent - dining menus and hours
        # "transport": Transport Agent - university bus timings and routes
        
        # Following PydanticAI best practices for usage limits
        self.usage_limits = UsageLimits(
            request_limit=20,  # Max requests per conversation
            total_tokens_limit=10000  # Max tokens per conversation
        )
        
        # Shared HTTP client for all agents (following PydanticAI dependency patterns)
        self.http_client = httpx.AsyncClient()

    async def route_message(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        message_history: Optional[list[ModelMessage]] = None,
        usage: Optional[Usage] = None
    ) -> Dict[str, Any]:
        """
        Route a user message to the appropriate agent based on intent classification.
        Follows PydanticAI programmatic agent hand-off pattern.

        Args:
            message: User's message
            user_id: Optional user ID for tracking
            message_history: Previous conversation messages
            usage: Usage tracking object to maintain across agents

        Returns:
            Dictionary containing the response and metadata
        """
        # Initialize usage tracking if not provided
        if usage is None:
            usage = Usage()
            
        try:
            # Step 1: Classify the intent (following PydanticAI usage pattern)
            intent = await self.intent_classifier.classify_intent(message, usage=usage)
            logger.info(f"Classified intent: {intent} for user: {user_id}")

            # Step 2: Route to appropriate agent with proper usage tracking
            agent_response = await self._route_to_agent(
                intent, message, user_id, message_history, usage
            )

            # Step 3: Return response with metadata including usage
            return {
                "response": agent_response,
                "intent": intent,
                "agent_used": self._get_agent_name(intent),
                "success": True,
                "usage": usage.dict() if hasattr(usage, 'dict') else str(usage)
            }

        except Exception as e:
            logger.error(f"Routing error for user {user_id}: {str(e)}")
            
            # Fallback to general agent with usage tracking
            try:
                fallback_response = await self.agents["general"].chat(
                    message, user_id, message_history=message_history, usage=usage,
                    http_client=self.http_client
                )
                return {
                    "response": fallback_response,
                    "intent": "general",
                    "agent_used": "General Assistant",
                    "success": False,
                    "error": "Routing failed, used fallback",
                    "usage": usage.dict() if hasattr(usage, 'dict') else str(usage)
                }
            except Exception as fallback_error:
                logger.error(f"Fallback agent also failed for user {user_id}: {str(fallback_error)}")
                return {
                    "response": "I apologize, but I'm experiencing technical difficulties. Please try again later.",
                    "intent": "error",
                    "agent_used": "None",
                    "success": False,
                    "error": "All agents failed",
                    "usage": usage.dict() if hasattr(usage, 'dict') else str(usage)
                }

    async def _route_to_agent(
        self, 
        intent: str, 
        message: str, 
        user_id: Optional[str] = None,
        message_history: Optional[list[ModelMessage]] = None,
        usage: Optional[Usage] = None
    ) -> str:
        """Route message to the appropriate agent based on intent with PydanticAI patterns."""
        
        if intent == "events":
            return await self.agents["events"].handle_events_query(
                message, user_id, message_history=message_history, usage=usage,
                http_client=self.http_client
            )
        elif intent == "general":
            return await self.agents["general"].chat(
                message, user_id, message_history=message_history, usage=usage,
                http_client=self.http_client
            )
        else:
            # Unknown intent, fallback to general
            logger.warning(f"Unknown intent {intent}, falling back to general agent")
            return await self.agents["general"].chat(
                message, user_id, message_history=message_history, usage=usage,
                http_client=self.http_client
            )

    def _get_agent_name(self, intent: str) -> str:
        """Get the display name of the agent handling the intent per Nexora Campus Copilot methodology."""
        agent_names = {
            "events": "Nexora Events Agent",
            "general": "Nexora General Assistant",
            # Future agents per methodology:
            # "schedule": "Nexora Schedule Agent",
            # "cafeteria": "Nexora Cafeteria Agent", 
            # "transport": "Nexora Transport Agent",
        }
        return agent_names.get(intent, "Nexora General Assistant")

    def add_agent(self, intent: str, agent: Any, agent_name: str) -> None:
        """
        Add a new specialized agent to the router.
        
        Args:
            intent: The intent category this agent handles
            agent: The agent instance
            agent_name: Display name for the agent
        """
        self.agents[intent] = agent
        logger.info(f"Added new agent: {agent_name} for intent: {intent}")

    def get_available_intents(self) -> list:
        """Get list of all available intent categories."""
        return list(self.agents.keys())

    async def cleanup(self) -> None:
        """Cleanup resources (HTTP client)."""
        if hasattr(self, 'http_client'):
            await self.http_client.aclose()


# Global router instance
agent_router = AgentRouter() 