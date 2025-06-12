"""
Pydantic models for the Nexora AI application.

This module contains all the data models used throughout the application,
organized by domain (chat, health, department, etc.).
"""

from .chat import ChatRequest, ChatResponse, EnhancedChatResponse
from .health import HealthResponse
from .department import Department, DepartmentResponse

__all__ = [
    # Chat models
    "ChatRequest",
    "ChatResponse",
    "EnhancedChatResponse",
    # Health models
    "HealthResponse",
    # Department models
    "Department",
    "DepartmentResponse",
]
