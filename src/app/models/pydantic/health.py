"""
Pydantic models for health check endpoints.

This module contains data models for health monitoring and status reporting.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Health check timestamp"
    )
