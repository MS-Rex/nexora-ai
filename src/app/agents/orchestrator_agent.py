from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import Usage
from pydantic_ai.messages import ModelMessage
from src.app.core.config.settings import settings
from src.app.agents.prompts.prompts_loader import agent_prompts_loader
from src.app.agents.tools.base import ToolDependencies
from src.app.agents.tools.department_tools import register_department_tools
from src.app.agents.tools.event_tools import register_event_tools
from src.app.agents.tools.datetime_tools import register_datetime_tools
from typing import Optional, Dict, Any
import logging
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorAgentDeps(ToolDependencies):
    """Dependencies for the Orchestrator Agent extending the base ToolDependencies."""
    pass


class OrchestratorAgent:
    """Single Orchestrator Agent for the Nexora Campus Copilot system.
    
    This agent replaces all specialized agents and routing logic. It has access to ALL tools
    and intelligently decides which tools to use based on the user's query. It can:
    - Handle single-domain queries (events only, departments only, general chat)
    - Handle multi-domain queries (events + departments, etc.)
    - Coordinate multiple tool calls and compose unified responses
    - Scale to new tools without architectural changes
    """

    def __init__(self):
        """Initialize the orchestrator agent with ALL available tools."""
        self.agent = self._create_agent()
        self.agent_name = agent_prompts_loader.get_agent_name(
            agent_type="orchestrator_agent", 
            agent_name="orchestrator_agent"
        )

    def _create_agent(self) -> Agent[OrchestratorAgentDeps]:
        """Create and configure the orchestrator agent with all available tools."""
        model_name = self._get_available_model()

        agent = Agent(
            model_name,
            deps_type=OrchestratorAgentDeps,
            instructions=agent_prompts_loader.get_system_instructions(
                agent_type="orchestrator_agent", 
                agent_name="orchestrator_agent"
            ),
        )

        # Register ALL available tools - the agent will decide which to use
        register_department_tools(agent, OrchestratorAgentDeps)
        register_event_tools(agent, OrchestratorAgentDeps)
        register_datetime_tools(agent, OrchestratorAgentDeps)
        
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

    async def handle_query(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        message_history: Optional[list[ModelMessage]] = None,
        usage: Optional[Usage] = None,
        http_client: Optional[httpx.AsyncClient] = None
    ) -> str:
        """
        Handle any user query by intelligently selecting and using appropriate tools.
        
        The agent will analyze the query and automatically:
        1. Determine which tools are needed (events, departments, both, or none)
        2. Make the necessary tool calls (potentially multiple, in parallel)
        3. Compose a unified, comprehensive response
        
        This replaces the need for intent classification and agent routing.

        Args:
            message: User's message (can be single or multi-domain)
            user_id: Optional user ID for tracking
            message_history: Previous conversation messages for context
            usage: Usage tracking object
            http_client: HTTP client for API calls (will create if not provided)

        Returns:
            Comprehensive response using appropriate tools
        """
        # Create HTTP client if not provided
        if http_client is None:
            http_client = httpx.AsyncClient()
            should_close_client = True
        else:
            should_close_client = False

        try:
            # Create dependencies for the agent
            deps = OrchestratorAgentDeps(
                http_client=http_client,
                base_api_url=settings.BASE_URL
            )

            # Let the agent analyze the query and use appropriate tools
            result = await self.agent.run(
                message,
                deps=deps,
                message_history=message_history,
                usage=usage
            )

            return result.output

        except Exception as e:
            logger.error(f"Orchestrator agent error for user {user_id}: {str(e)}")
            return agent_prompts_loader.get_error_message(
                "general_error", 
                agent_type="orchestrator_agent", 
                agent_name="orchestrator_agent"
            )
        finally:
            # Close the client if we created it
            if should_close_client:
                await http_client.aclose()


# Global orchestrator agent instance
orchestrator_agent = OrchestratorAgent() 