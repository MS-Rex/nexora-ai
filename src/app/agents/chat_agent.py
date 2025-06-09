from pydantic_ai import Agent
from src.app.core.config.settings import settings
from src.app.agents.prompts.prompts_loader import agent_prompts_loader
from typing import Optional


class ChatAgentService:
    """Service class for managing the PydanticAI chat agent."""

    def __init__(self):
        """Initialize the chat agent with available AI model."""
        self.agent = self._create_agent()
        self.agent_name = agent_prompts_loader.get_agent_name()

    def _create_agent(self) -> Agent:
        """Create and configure the PydanticAI agent."""

        model_name = self._get_available_model()

        agent = Agent(
            model_name,
            instructions=agent_prompts_loader.get_system_instructions(),
        )

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



    async def chat(self, message: str, user_id: Optional[str] = None) -> str:
        """
        Send a message to the agent and get a response.

        Args:
            message: User's message
            user_id: Optional user ID for internal logging/tracking (not sent to AI)

        Returns:
            Agent's response as a string
        """
        try:
            # TODO: Storing conversation history

            result = await self.agent.run(message)

            return result.output

        except Exception as e:
            # TODO: Log the error with user_id for debugging (but don't expose user_id)
            # logger.error(f"Chat error for user {user_id}: {str(e)}")

            # Fallback response for errors
            return agent_prompts_loader.get_error_message("general_error")


# Global agent instance
chat_agent_service = ChatAgentService()
