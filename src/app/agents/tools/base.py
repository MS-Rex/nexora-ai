"""
Base classes and utilities for PydanticAI tools.

This module provides common functionality and patterns for creating tools
that can be used across different agents in the Nexora AI system.
"""

from typing import Protocol, Dict, Any, Optional
import httpx
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolDependencies:
    """Common dependencies that tools might need."""
    http_client: httpx.AsyncClient
    base_api_url: str = "http://127.0.0.1:8000/api"


class ToolError(Exception):
    """Base exception for tool-related errors."""
    pass


class HTTPToolError(ToolError):
    """Exception for HTTP-related tool errors."""
    pass


class Tool(Protocol):
    """Protocol for defining tools that can be used by agents."""
    
    async def execute(self, dependencies: ToolDependencies, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given dependencies and parameters."""
        ...


async def handle_http_request(
    client: httpx.AsyncClient, 
    url: str, 
    method: str = "GET",
    **kwargs
) -> Dict[str, Any]:
    """
    Common HTTP request handler with error handling.
    
    Args:
        client: HTTP client to use
        url: URL to request
        method: HTTP method (GET, POST, etc.)
        **kwargs: Additional arguments passed to the HTTP client
        
    Returns:
        Response data or error information
    """
    try:
        logger.info(f"Making {method} request to: {url}")
        
        if method.upper() == "GET":
            response = await client.get(url, **kwargs)
        elif method.upper() == "POST":
            response = await client.post(url, **kwargs)
        else:
            raise HTTPToolError(f"Unsupported HTTP method: {method}")
            
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Successfully received response from {url}")
        return {"data": data, "success": True}
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error for {url}: {str(e)}")
        return {"error": f"HTTP request failed: {str(e)}", "success": False}
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}", "success": False} 