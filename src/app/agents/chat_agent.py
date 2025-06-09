from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import Usage
from pydantic_ai.messages import ModelMessage
from src.app.core.config.settings import settings
from src.app.agents.prompts.prompts_loader import agent_prompts_loader
from src.app.models.pydantic.department import Department, DepartmentResponse
from src.app.agents.tools.base import ToolDependencies
from src.app.agents.tools.department_tools import register_department_tools
from typing import Optional, Dict, Any
import logging
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass 
class ChatAgentDeps(ToolDependencies):
    """Dependencies for the Chat Agent extending the base ToolDependencies."""
    pass


class ChatAgentService:
    """Service class for managing the PydanticAI chat agent and multi-agent routing."""

    def __init__(self):
        """Initialize the chat agent with available AI model."""
        self.agent = self._create_agent()
        self.agent_name = agent_prompts_loader.get_agent_name()

    def _create_agent(self) -> Agent[ChatAgentDeps]:
        """Create and configure the PydanticAI agent."""

        model_name = self._get_available_model()

        agent = Agent(
            model_name,
            deps_type=ChatAgentDeps,
            instructions=agent_prompts_loader.get_system_instructions(),
        )

        # Register department tools using the new tools module
        register_department_tools(agent, ChatAgentDeps)

        return agent

    def _get_available_model(self) -> str:
        """Get the first available AI model based on API keys."""
        if settings.OPENAI_API_KEY:
            return "openai:gpt-4o-mini"
        elif settings.ANTHROPIC_API_KEY:
            return "anthropic:claude-3-5-haiku-latest"
        else:
            # Fallback to test model for development
            return "test"

    async def chat(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        message_history: Optional[list[ModelMessage]] = None,
        usage: Optional[Usage] = None,
        http_client: Optional[httpx.AsyncClient] = None
    ) -> str:
        """
        Send a message to the agent and get a response.
        This method is used by the router for general queries.
        Follows PydanticAI programmatic hand-off patterns.

        Args:
            message: User's message
            user_id: Optional user ID for internal logging/tracking (not sent to AI)
            message_history: Previous conversation messages for context
            usage: Usage tracking object
            http_client: HTTP client for API calls (will create if not provided)

        Returns:
            Agent's response as a string
        """
        # Create HTTP client if not provided
        if http_client is None:
            http_client = httpx.AsyncClient()
            should_close_client = True
        else:
            should_close_client = False

        try:
            # Create dependencies for the agent using the new ToolDependencies structure
            deps = ChatAgentDeps(
                http_client=http_client,
                base_api_url="http://127.0.0.1:8000/api"
            )

            # Use PydanticAI patterns for message history and usage tracking
            result = await self.agent.run(
                message,
                deps=deps,
                message_history=message_history,
                usage=usage
            )

            return result.output

        except Exception as e:
            logger.error(f"Chat error for user {user_id}: {str(e)}")

            # Fallback response for errors
            return agent_prompts_loader.get_error_message("general_error")
        finally:
            # Close the client if we created it
            if should_close_client:
                await http_client.aclose()

    async def chat_with_routing(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a message through the multi-agent system with intent classification and routing.

        Args:
            message: User's message
            user_id: Optional user ID for tracking

        Returns:
            Dictionary containing response and metadata about which agent was used
        """
        # Import here to avoid circular imports
        from src.app.agents.agent_router import agent_router
        
        return await agent_router.route_message(message, user_id)


# Global agent instance
chat_agent_service = ChatAgentService()
