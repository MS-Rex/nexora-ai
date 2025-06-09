"""
User-related tools for PydanticAI agents.

These tools can be used by any agent that needs to fetch user profile information.
"""

from typing import Dict, Any, Optional
from pydantic_ai import Agent, RunContext
from src.app.agents.tools.base import ToolDependencies, handle_http_request
import logging

logger = logging.getLogger(__name__)


def register_user_tools(agent: Agent, deps_type: type) -> None:
    """
    Register user-related tools with a PydanticAI agent.
    
    Args:
        agent: The PydanticAI agent to register tools with
        deps_type: The dependencies type that should include ToolDependencies
    """
    
    @agent.tool
    async def get_user_data(ctx: RunContext) -> Dict[str, Any]:
        """
        Fetch user profile data for the current user from the campus user API.
        The user_id is automatically obtained from the request context.
            
        Returns:
            User profile information for the current user
        """
        try:
            # Get user_id from dependencies (automatically passed from request context)
            user_id = ctx.deps.user_id
            
            if not user_id:
                return {
                    "error": "User ID is required to fetch user data. Please ensure you are logged in.",
                    "success": False
                }
            
            url = f"{ctx.deps.base_api_url}/user/fetch"
            
            # Convert user_id to int if it's a string
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                return {
                    "error": "Invalid user ID format.",
                    "success": False
                }
            
            # Prepare the request body with user_id
            request_body = {"user_id": user_id_int}
            
            # Use common HTTP handler with POST method
            result = await handle_http_request(
                ctx.deps.http_client, 
                url, 
                method="POST",
                json=request_body
            )
            
            if result["success"]:
                user_data = result["data"]
                logger.info(f"Successfully fetched user data for user {user_id_int}")
                return {
                    "user_id": user_id_int,
                    "user_data": user_data,
                    "success": True
                }
            else:
                logger.error(f"Failed to fetch user data for user {user_id_int}: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            logger.error(f"Unexpected error in get_user_data for user {ctx.deps.user_id}: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}


class UserTools:
    """
    Standalone user tools that can be used without PydanticAI agents.
    Useful for testing or direct API access.
    """
    
    @staticmethod
    async def get_user_data_direct(
        dependencies: ToolDependencies, 
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Direct user data fetching without PydanticAI context."""
        # Use user_id from parameter if provided, otherwise try to get from dependencies
        if user_id is None and hasattr(dependencies, 'user_id') and dependencies.user_id:
            try:
                user_id = int(dependencies.user_id)
            except (ValueError, TypeError):
                return {"error": "Invalid user ID format.", "success": False}
        
        if user_id is None:
            return {"error": "User ID is required to fetch user data.", "success": False}
        
        url = f"{dependencies.base_api_url}/user/fetch"
        request_body = {"user_id": user_id}
        
        result = await handle_http_request(
            dependencies.http_client, 
            url, 
            method="POST",
            json=request_body
        )
        
        if result["success"]:
            return {
                "user_id": user_id,
                "user_data": result["data"],
                "success": True
            }
        else:
            return result 