"""
Nexora Campus Copilot AI System.

SIMPLIFIED ARCHITECTURE:
- Single Orchestrator Agent with intelligent tool selection
- No complex routing or intent classification needed
- Agent automatically selects appropriate tools based on query context
- Handles single-domain, multi-domain, and general conversation seamlessly

The orchestrator approach replaces the need for multiple specialized agents,
intent classification, and complex routing logic with a single intelligent agent.
"""

# Single Orchestrator Architecture
from .orchestrator_agent import OrchestratorAgent, orchestrator_agent
from .nexora_service import NexoraService, nexora_service

__all__ = [
    # Orchestrator Agent (Main Components)
    "OrchestratorAgent",     # Single agent with intelligent tool selection
    "NexoraService",         # Simplified service interface
    "orchestrator_agent",    # Global orchestrator instance
    "nexora_service",        # Global service instance
]
