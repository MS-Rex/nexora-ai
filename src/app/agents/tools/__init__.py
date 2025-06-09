"""
Tools module for PydanticAI agents.

This module provides reusable tools that can be shared across different agents
in the Nexora AI system. Tools are organized by domain (departments, events, etc.)
and can be registered with agents or used directly.
"""

from .base import ToolDependencies, ToolError, HTTPToolError, handle_http_request
from .department_tools import register_department_tools, DepartmentTools
from .event_tools import register_event_tools, EventTools

__all__ = [
    # Base utilities
    "ToolDependencies",
    "ToolError", 
    "HTTPToolError",
    "handle_http_request",
    
    # Department tools
    "register_department_tools",
    "DepartmentTools",
    
    # Event tools
    "register_event_tools", 
    "EventTools",
] 