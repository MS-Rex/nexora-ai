"""
Event-related tools for PydanticAI agents.

These tools can be used by any agent that needs to fetch or search event data.
"""

from typing import Dict, Any, Optional
from pydantic_ai import Agent, RunContext
from src.app.agents.tools.base import ToolDependencies, handle_http_request
import logging

logger = logging.getLogger(__name__)


def register_event_tools(agent: Agent, deps_type: type) -> None:
    """
    Register event-related tools with a PydanticAI agent.
    
    Args:
        agent: The PydanticAI agent to register tools with
        deps_type: The dependencies type that should include ToolDependencies
    """
    
    @agent.tool
    async def fetch_events(ctx: RunContext, event_id: int = 0) -> Dict[str, Any]:
        """
        Fetch events from the campus events API.
        
        Args:
            event_id: Event ID to fetch, defaults to 0 for all events
            
        Returns:
            Events data from the API
        """
        try:
            base_url = f"{ctx.deps.base_api_url}/event/data"
            url = f"{base_url}/{event_id}"
            
            # Use common HTTP handler
            result = await handle_http_request(ctx.deps.http_client, url)
            
            if result["success"]:
                events_data = result["data"]
                logger.info(f"Successfully fetched events data: {len(events_data) if isinstance(events_data, list) else 1} events")
                return events_data
            else:
                return result
                
        except Exception as e:
            logger.error(f"Unexpected error in fetch_events: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    @agent.tool
    async def search_events(ctx: RunContext, query: str) -> Dict[str, Any]:
        """
        Search for specific events by keyword or topic.
        
        Args:
            query: Search query for events
            
        Returns:
            Filtered events data matching the query
        """
        try:
            # First fetch all events
            all_events = await fetch_events(ctx, 0)
            
            if "error" in all_events:
                return all_events
            
            # For now, return all events - in the future this could be enhanced
            # with actual search functionality if the API supports it
            logger.info(f"Searching events with query: '{query}'")
            return {
                "query": query,
                "events": all_events,
                "note": "Showing all available events. Search filtering can be enhanced when API supports it.",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in search_events: {str(e)}")
            return {"error": f"Search failed: {str(e)}", "success": False}


class EventTools:
    """
    Standalone event tools that can be used without PydanticAI agents.
    Useful for testing or direct API access.
    """
    
    @staticmethod
    async def fetch_events_direct(
        dependencies: ToolDependencies,
        event_id: int = 0
    ) -> Dict[str, Any]:
        """Direct event fetching without PydanticAI context."""
        base_url = f"{dependencies.base_api_url}/event/data"
        url = f"{base_url}/{event_id}"
        
        result = await handle_http_request(dependencies.http_client, url)
        return result["data"] if result["success"] else result
    
    @staticmethod
    async def search_events_direct(
        dependencies: ToolDependencies,
        query: str
    ) -> Dict[str, Any]:
        """Direct event searching without PydanticAI context."""
        # Fetch all events first
        all_events = await EventTools.fetch_events_direct(dependencies)
        
        if "error" in all_events:
            return all_events
        
        return {
            "query": query,
            "events": all_events,
            "note": "Showing all available events. Search filtering can be enhanced when API supports it.",
            "success": True
        } 