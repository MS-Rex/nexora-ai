from pydantic_ai import Agent
from pydantic_ai.usage import Usage
from src.app.core.config.settings import settings
from src.app.agents.prompts.prompts_loader import agent_prompts_loader
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RouterAgent:
    """Central Router Agent (Intention Classifier) serving as the main entry point for user queries.

    This agent is responsible for understanding the user's intent and dispatching the request
    to the appropriate specialized agent according to the Nexora Campus Copilot methodology.
    """

    def __init__(self):
        """Initialize the router agent (intention classifier)."""
        self.agent = self._create_agent()
        self.agent_name = agent_prompts_loader.get_agent_name(
            agent_type="intent_classifier", agent_name="intent_classifier"
        )

    def _create_agent(self) -> Agent:
        """Create and configure the router agent (intention classifier)."""
        model_name = self._get_available_model()

        agent = Agent(
            model_name,
            instructions=agent_prompts_loader.get_system_instructions(
                agent_type="intent_classifier", agent_name="intent_classifier"
            ),
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

    async def classify_intent(self, message: str, usage: Optional[Usage] = None) -> str:
        """
        Classify the user's message to determine intent.
        Follows PydanticAI usage tracking patterns.

        Args:
            message: User's message to classify
            usage: Usage object for tracking tokens across agents

        Returns:
            Intent category as a string (e.g., "events", "general")
        """
        try:
            # Pass usage to agent.run for proper tracking
            result = await self.agent.run(message, usage=usage)
            intent = result.output.strip().lower()

            # Validate intent is one of our known categories for Nexora Campus Copilot
            # Currently implemented: Events Agent, General Chat
            # Future agents per methodology: Schedule Agent, Cafeteria Agent, Transport Agent
            valid_intents = ["events", "general"]
            if intent in valid_intents:
                return intent
            else:
                logger.warning(
                    f"Unknown intent classified: {intent}, defaulting to general"
                )
                return "general"

        except Exception as e:
            logger.error(f"Intent classification error: {str(e)}")
            return agent_prompts_loader.get_fallback_response(
                "unknown_intent",
                agent_type="intent_classifier",
                agent_name="intent_classifier",
            )


# Global router agent instance (following Nexora Campus Copilot methodology)
router_agent = RouterAgent()

# Backward compatibility alias
intent_classifier_agent = router_agent
