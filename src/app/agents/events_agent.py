from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import Usage
from pydantic_ai.messages import ModelMessage
from src.app.core.config.settings import settings
from src.app.agents.prompts.prompts_loader import agent_prompts_loader
from typing import Optional, Dict, Any
import logging
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EventsAgentDeps:
    """Dependencies for the Events Agent following PydanticAI patterns."""
    http_client: httpx.AsyncClient
    events_api_base_url: str = "http://127.0.0.1:8000/api/event/data"


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

        # Add tools for fetching events
        self._register_tools(agent)
        return agent

    def _register_tools(self, agent: Agent[EventsAgentDeps]) -> None:
        """Register tools for the events agent."""
        
        @agent.tool
        async def fetch_events(ctx: RunContext[EventsAgentDeps], event_id: int = 0) -> Dict[str, Any]:
            """
            Fetch events from the campus events API.
            
            Args:
                event_id: Event ID to fetch, defaults to 0 for all events
                
            Returns:
                Events data from the API
            """
            try:
                url = f"{ctx.deps.events_api_base_url}/{event_id}"
                logger.info(f"Fetching events from: {url}")
                
                response = await ctx.deps.http_client.get(url)
                response.raise_for_status()
                
                events_data = response.json()
                logger.info(f"Successfully fetched events data: {len(events_data) if isinstance(events_data, list) else 1} events")
                
                return events_data
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching events: {str(e)}")
                return {"error": f"Failed to fetch events: {str(e)}"}
            except Exception as e:
                logger.error(f"Unexpected error fetching events: {str(e)}")
                return {"error": f"Unexpected error: {str(e)}"}

        @agent.tool
        async def search_events(ctx: RunContext[EventsAgentDeps], query: str) -> Dict[str, Any]:
            """
            Search for specific events by keyword or topic.
            
            Args:
                query: Search query for events
                
            Returns:
                Filtered events data matching the query
            """
            try:
                # First fetch all events
                all_events = await fetch_events(ctx, 0)
                
                if "error" in all_events:
                    return all_events
                
                # For now, return all events - in the future this could be enhanced
                # with actual search functionality if the API supports it
                logger.info(f"Searching events with query: {query}")
                return {
                    "query": query,
                    "events": all_events,
                    "note": "Showing all available events. Search filtering can be enhanced when API supports it."
                }
                
            except Exception as e:
                logger.error(f"Error searching events: {str(e)}")
                return {"error": f"Search failed: {str(e)}"}

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
            # Create dependencies for the agent
            deps = EventsAgentDeps(
                http_client=http_client,
                events_api_base_url="http://127.0.0.1:8000/api/event/data"
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