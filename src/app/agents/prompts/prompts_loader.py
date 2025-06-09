import yaml
import os
from pathlib import Path
from typing import Dict, Any
from functools import lru_cache


class AgentPromptsLoader:
    """Utility class for loading agent prompts from YAML configuration files."""

    def __init__(self):
        self.prompts_dir = Path(__file__).parent

    @lru_cache(maxsize=10)
    def load_agent_prompts(self, agent_type: str = "chat_agent") -> Dict[str, Any]:
        """Load prompts for a specific agent type with caching."""
        prompts_file = self.prompts_dir / f"{agent_type}_prompts.yaml"

        try:
            with open(prompts_file, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompts file not found: {prompts_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing prompts YAML file: {e}")

    def get_agent_config(
        self, agent_type: str = "chat_agent", agent_name: str = "nexora_ai_assistant"
    ) -> Dict[str, Any]:
        """Get configuration for a specific agent."""
        prompts = self.load_agent_prompts(agent_type)
        if agent_name not in prompts:
            raise KeyError(
                f"Agent '{agent_name}' not found in {agent_type} prompts configuration"
            )
        return prompts[agent_name]

    def get_system_instructions(
        self, agent_type: str = "chat_agent", agent_name: str = "nexora_ai_assistant"
    ) -> str:
        """Get system instructions for an agent."""
        config = self.get_agent_config(agent_type, agent_name)
        return config.get("system_instructions", "")

    def get_agent_name(
        self, agent_type: str = "chat_agent", agent_name: str = "nexora_ai_assistant"
    ) -> str:
        """Get the display name for an agent."""
        config = self.get_agent_config(agent_type, agent_name)
        return config.get("agent_name", "AI Assistant")

    def get_error_message(
        self,
        error_type: str = "general_error",
        agent_type: str = "chat_agent",
        agent_name: str = "nexora_ai_assistant",
    ) -> str:
        """Get an error message for an agent."""
        config = self.get_agent_config(agent_type, agent_name)
        error_messages = config.get("error_messages", {})
        return error_messages.get(error_type, "An error occurred. Please try again.")

    def get_fallback_response(
        self,
        response_type: str,
        agent_type: str = "chat_agent",
        agent_name: str = "nexora_ai_assistant",
    ) -> str:
        """Get a fallback response for an agent."""
        config = self.get_agent_config(agent_type, agent_name)
        fallback_responses = config.get("fallback_responses", {})
        return fallback_responses.get(response_type, "Service unavailable.")


# Global instance
agent_prompts_loader = AgentPromptsLoader()
