"""
Multi-agent system for Nexora Campus Copilot.

This module implements the scalable agentic architecture methodology with:
- Central Router Agent (Intention Classifier) as main entry point
- Specialized agents for campus services (Events Agent currently implemented)
- Extensible router for adding future agents (Schedule, Cafeteria, Transport per methodology)
- PydanticAI-based programmatic agent hand-off pattern
"""

from .chat_agent import ChatAgentService, chat_agent_service
from .intent_classifier_agent import RouterAgent, router_agent, intent_classifier_agent
from .events_agent import EventsAgent, events_agent
from .agent_router import AgentRouter, agent_router

__all__ = [
    # Main service classes (Nexora Campus Copilot methodology)
    "ChatAgentService",
    "RouterAgent",           # Central Router Agent (Intention Classifier)
    "EventsAgent",           # Events Agent for campus events
    "AgentRouter",
    
    # Global instances
    "chat_agent_service",
    "router_agent",          # New primary name following methodology
    "intent_classifier_agent",  # Backward compatibility alias
    "events_agent", 
    "agent_router",
]
