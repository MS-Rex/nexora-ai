from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import Usage
from pydantic_ai.messages import ModelMessage
from src.app.core.config.settings import settings
from src.app.agents.prompts.prompts_loader import agent_prompts_loader
from src.app.agents.tools.base import (
    ToolDependencies,
    format_datetime_context_for_prompt,
    generate_datetime_context,
)
from src.app.agents.tools.department_tools import register_department_tools
from src.app.agents.tools.event_tools import register_event_tools
from src.app.agents.tools.bus_tools import register_bus_tools
from src.app.agents.tools.cafeteria_tools import register_cafeteria_tools
from src.app.agents.tools.exam_tools import register_exam_tools
from src.app.agents.tools.user_tools import register_user_tools
from src.app.services.rag_service import rag_service
from typing import Optional, Dict, Any
import logging
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorAgentDeps(ToolDependencies):
    """Dependencies for the Orchestrator Agent extending the base ToolDependencies."""

    user_id: Optional[str] = None


class OrchestratorAgent:
    """Single Orchestrator Agent for the Nexora Campus Copilot system.

    This agent replaces all specialized agents and routing logic. It has access to ALL tools
    and intelligently decides which tools to use based on the user's query. It can:
    - Handle single-domain queries (events only, departments only, bus routes only, cafeteria menus only, exam results only, user profile only, general chat)
    - Handle multi-domain queries (events + departments + bus routes + cafeteria + exam results + user profile, etc.)
    - Handle knowledge-based queries using automatically injected RAG context
    - Coordinate multiple tool calls and compose unified responses
    - Scale to new tools without architectural changes
    """

    def __init__(self):
        """Initialize the orchestrator agent with ALL available tools."""
        self.agent = self._create_agent()
        self.agent_name = agent_prompts_loader.get_agent_name(
            agent_type="orchestrator_agent", agent_name="orchestrator_agent"
        )

    def _create_agent(self) -> Agent[OrchestratorAgentDeps]:
        """Create and configure the orchestrator agent with all available tools."""
        model_name = self._get_available_model()

        agent = Agent(
            model_name,
            deps_type=OrchestratorAgentDeps,
            instructions=agent_prompts_loader.get_system_instructions(
                agent_type="orchestrator_agent", agent_name="orchestrator_agent"
            ),
        )

        # Register ALL available tools - the agent will decide which to use
        register_department_tools(agent, OrchestratorAgentDeps)
        register_event_tools(agent, OrchestratorAgentDeps)
        register_bus_tools(agent, OrchestratorAgentDeps)
        register_cafeteria_tools(agent, OrchestratorAgentDeps)
        register_exam_tools(agent, OrchestratorAgentDeps)
        register_user_tools(agent, OrchestratorAgentDeps)

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

    async def _get_rag_context(self, message: str) -> str:
        """
        Automatically retrieve relevant context from the knowledge base for the user's message.

        Args:
            message: User's message to search for relevant context

        Returns:
            Formatted context string from the knowledge base, or empty string if no relevant context found
        """
        try:
            # Check if knowledge base is loaded
            if not rag_service.is_knowledge_base_loaded():
                logger.warning(
                    "Knowledge base is not loaded, skipping RAG context retrieval"
                )
                return ""

            # Search for relevant context with reasonable defaults
            results = rag_service.search_knowledge(
                query=message,
                query_type="hybrid",
                limit=5,  # Limit to top 5 most relevant results
            )

            if not results:
                logger.debug(
                    f"No relevant knowledge base results found for query: {message[:50]}..."
                )
                return ""

            # Format the context in a structured way
            context_parts = ["**Knowledge Base Context:**\n"]

            for i, result in enumerate(results, 1):
                text = result.get("text", "")
                source = result.get("source_file", "unknown")
                score = result.get("_relevance_score", 0)

                # Only include results with reasonable relevance scores
                if score >= settings.RAG_SIMILARITY_THRESHOLD:
                    context_parts.append(
                        f"**Source {i}: {source} (Relevance: {score:.2f})**"
                    )
                    context_parts.append(text)
                    context_parts.append("---")

            # Only return context if we have relevant results
            if len(context_parts) > 1:  # More than just the header
                context_parts.append("\n**End of Knowledge Base Context**\n")
                return "\n".join(context_parts)

            return ""

        except Exception as e:
            logger.error(f"Error retrieving RAG context: {e}")
            return ""

    async def handle_query(
        self,
        message: str,
        user_id: Optional[str] = None,
        message_history: Optional[list[ModelMessage]] = None,
        usage: Optional[Usage] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> str:
        """
        Handle any user query by automatically injecting RAG context and datetime context, then using appropriate tools.

        The agent will:
        1. Automatically retrieve relevant context from the knowledge base
        2. Generate current datetime context
        3. Inject both contexts into the message before processing
        4. Analyze the query and automatically determine which tools are needed
        5. Make the necessary tool calls (potentially multiple, in parallel)
        6. Compose a unified, comprehensive response

        This eliminates the need for RAG tool calls and datetime tool calls by providing context automatically.

        Args:
            message: User's message (can be single or multi-domain)
            user_id: Optional user ID for tracking
            message_history: Previous conversation messages for context
            usage: Usage tracking object
            http_client: HTTP client for API calls (will create if not provided)

        Returns:
            Comprehensive response using appropriate tools with RAG and datetime context
        """
        # Create HTTP client if not provided
        if http_client is None:
            http_client = httpx.AsyncClient()
            should_close_client = True
        else:
            should_close_client = False

        try:
            # Automatically retrieve RAG context before processing
            rag_context = await self._get_rag_context(message)

            # Generate fresh datetime context for this query
            datetime_context = generate_datetime_context()
            formatted_datetime_context = format_datetime_context_for_prompt(
                datetime_context
            )

            # Enhance the message with both RAG and datetime context
            enhanced_message_parts = [formatted_datetime_context]

            if rag_context:
                enhanced_message_parts.append(rag_context)
                logger.info(f"Enhanced message with RAG context for user {user_id}")
            else:
                logger.debug(f"No RAG context found for user {user_id}")

            enhanced_message_parts.append(f"**User Query:** {message}")
            enhanced_message = "\n\n".join(enhanced_message_parts)

            # Create dependencies for the agent with fresh datetime context
            deps = OrchestratorAgentDeps(
                http_client=http_client,
                base_api_url=settings.BASE_URL,
                user_id=user_id,
                datetime_context=datetime_context,  # Fresh datetime context for each query
            )

            # Let the agent analyze the enhanced query and use appropriate tools
            result = await self.agent.run(
                enhanced_message,
                deps=deps,
                message_history=message_history,
                usage=usage,
            )

            return result.output

        except Exception as e:
            logger.error(f"Orchestrator agent error for user {user_id}: {str(e)}")
            return agent_prompts_loader.get_error_message(
                "general_error",
                agent_type="orchestrator_agent",
                agent_name="orchestrator_agent",
            )
        finally:
            # Close the client if we created it
            if should_close_client:
                await http_client.aclose()


# Global orchestrator agent instance
orchestrator_agent = OrchestratorAgent()
