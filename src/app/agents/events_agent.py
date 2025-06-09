from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import Usage
from pydantic_ai.messages import ModelMessage
from src.app.core.config.settings import settings
from src.app.agents.prompts.prompts_loader import agent_prompts_loader
from src.app.agents.tools.base import ToolDependencies
from src.app.agents.tools.event_tools import register_event_tools
from typing import Optional, Dict, Any
import logging
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EventsAgentDeps(ToolDependencies):
    """Dependencies for the Events Agent extending the base ToolDependencies."""
    pass


class EventsAgent:
    """Events Agent for Nexora Campus Copilot system.
    
    Specialized agent responsible for handling campus events, schedules, and reminders
    according to the Nexora Campus Copilot methodology.
    """

    def __init__(self):
        """Initialize the events agent."""
        self.agent = self._create_agent()
        self.agent_name = agent_prompts_loader.get_agent_name(
            agent_type="events_agent", 
            agent_name="events_agent"
        )

    def _create_agent(self) -> Agent[EventsAgentDeps]:
        """Create and configure the events agent with dependencies."""
        model_name = self._get_available_model()

        agent = Agent(
            model_name,
            deps_type=EventsAgentDeps,
            instructions=agent_prompts_loader.get_system_instructions(
                agent_type="events_agent", 
                agent_name="events_agent"
            ),
        )

        # Register event tools using the new tools module
        register_event_tools(agent, EventsAgentDeps)
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

    async def handle_events_query(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        message_history: Optional[list[ModelMessage]] = None,
        usage: Optional[Usage] = None,
        http_client: Optional[httpx.AsyncClient] = None
    ) -> str:
        """
        Handle events-related queries and requests.
        Follows PydanticAI programmatic hand-off patterns with real events API integration.

        Args:
            message: User's message about events
            user_id: Optional user ID for tracking
            message_history: Previous conversation messages for context
            usage: Usage tracking object
            http_client: HTTP client for API calls (will create if not provided)

        Returns:
            Agent's response about events
        """
        # Create HTTP client if not provided
        if http_client is None:
            http_client = httpx.AsyncClient()
            should_close_client = True
        else:
            should_close_client = False

        try:
            # Create dependencies for the agent using the new ToolDependencies structure
            deps = EventsAgentDeps(
                http_client=http_client,
                base_api_url="http://127.0.0.1:8000/api"
            )

            # Use PydanticAI patterns: pass deps, message_history and usage
            result = await self.agent.run(
                message, 
                deps=deps,
                message_history=message_history,
                usage=usage
            )
            return result.output

        except Exception as e:
            logger.error(f"Events agent error for user {user_id}: {str(e)}")
            return agent_prompts_loader.get_error_message(
                "general_error", 
                agent_type="events_agent", 
                agent_name="events_agent"
            )
        finally:
            # Close the client if we created it
            if should_close_client:
                await http_client.aclose()

    async def set_reminder(self, event_details: str, user_id: Optional[str] = None) -> str:
        """
        Set a reminder for an event (placeholder for future implementation).

        Args:
            event_details: Details about the event to set reminder for
            user_id: Optional user ID for reminder association

        Returns:
            Confirmation message about reminder
        """
        try:
            # TODO: Implement actual reminder functionality:
            # - Store reminder in database
            # - Schedule notification
            # - Integrate with notification service

            return agent_prompts_loader.get_fallback_response(
                "reminder_unavailable", 
                agent_type="events_agent", 
                agent_name="events_agent"
            )

        except Exception as e:
            logger.error(f"Reminder setting error for user {user_id}: {str(e)}")
            return agent_prompts_loader.get_error_message(
                "general_error", 
                agent_type="events_agent", 
                agent_name="events_agent"
            )


# Global events agent instance
events_agent = EventsAgent() 