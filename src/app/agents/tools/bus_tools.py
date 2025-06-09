"""
Bus route-related tools for PydanticAI agents.

These tools can be used by any agent that needs to fetch or search bus route data.
"""

from typing import Dict, Any, Optional
from pydantic_ai import Agent, RunContext
from src.app.agents.tools.base import ToolDependencies, handle_http_request
import logging

logger = logging.getLogger(__name__)


def register_bus_tools(agent: Agent, deps_type: type) -> None:
    """
    Register bus route-related tools with a PydanticAI agent.
    
    Args:
        agent: The PydanticAI agent to register tools with
        deps_type: The dependencies type that should include ToolDependencies
    """
    
    @agent.tool
    async def fetch_bus_routes(ctx: RunContext, route_id: int = 0) -> Dict[str, Any]:
        """
        Fetch bus routes from the campus bus route API.
        
        Args:
            route_id: Route ID to fetch, defaults to 0 for all routes
            
        Returns:
            Bus routes data from the API
        """
        try:
            base_url = f"{ctx.deps.base_api_url}/bus/route"
            url = f"{base_url}/{route_id}"
            
            # Use common HTTP handler
            result = await handle_http_request(ctx.deps.http_client, url)
            
            if result["success"]:
                routes_data = result["data"]
                logger.info(f"Successfully fetched bus routes data: {len(routes_data) if isinstance(routes_data, list) else 1} routes")
                return routes_data
            else:
                return result
                
        except Exception as e:
            logger.error(f"Unexpected error in fetch_bus_routes: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    @agent.tool
    async def search_bus_routes(ctx: RunContext, query: str) -> Dict[str, Any]:
        """
        Search for specific bus routes by route name, start point, end point, or route number.
        
        Args:
            query: Search query for bus routes (can be route name, start/end point, route number, etc.)
            
        Returns:
            Filtered bus routes data matching the query
        """
        try:
            # First fetch all routes
            all_routes = await fetch_bus_routes(ctx, 0)
            
            if "error" in all_routes:
                return all_routes
            
            # Filter routes based on the query
            query_lower = query.lower()
            filtered_routes = []
            
            if isinstance(all_routes, list):
                for route in all_routes:
                    # Search in route_name, route_number, start_point, end_point
                    route_name = str(route.get("route_name", "")).lower()
                    route_number = str(route.get("route_number", "")).lower()
                    start_point = str(route.get("start_point", "")).lower()
                    end_point = str(route.get("end_point", "")).lower()
                    
                    if (query_lower in route_name or 
                        query_lower in route_number or 
                        query_lower in start_point or 
                        query_lower in end_point):
                        filtered_routes.append(route)
            
            logger.info(f"Searching bus routes with query: '{query}', found {len(filtered_routes)} matches")
            return {
                "query": query,
                "routes": filtered_routes,
                "total_found": len(filtered_routes),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in search_bus_routes: {str(e)}")
            return {"error": f"Search failed: {str(e)}", "success": False}

    @agent.tool
    async def get_routes_by_status(ctx: RunContext, status: str) -> Dict[str, Any]:
        """
        Get bus routes filtered by their current status.
        
        Args:
            status: Route status to filter by (e.g., "On Time", "Delayed", "Cancelled")
            
        Returns:
            Bus routes data filtered by status
        """
        try:
            # First fetch all routes
            all_routes = await fetch_bus_routes(ctx, 0)
            
            if "error" in all_routes:
                return all_routes
            
            # Filter routes by status
            status_lower = status.lower()
            filtered_routes = []
            
            if isinstance(all_routes, list):
                for route in all_routes:
                    route_status = str(route.get("status", "")).lower()
                    if status_lower in route_status:
                        filtered_routes.append(route)
            
            logger.info(f"Filtering bus routes by status: '{status}', found {len(filtered_routes)} matches")
            return {
                "status": status,
                "routes": filtered_routes,
                "total_found": len(filtered_routes),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in get_routes_by_status: {str(e)}")
            return {"error": f"Status filter failed: {str(e)}", "success": False}

    @agent.tool
    async def get_routes_by_time_range(ctx: RunContext, start_time: str, end_time: str) -> Dict[str, Any]:
        """
        Get bus routes that depart within a specific time range.
        
        Args:
            start_time: Start time in HH:MM format (e.g., "07:00")
            end_time: End time in HH:MM format (e.g., "08:00")
            
        Returns:
            Bus routes data filtered by departure time range
        """
        try:
            # First fetch all routes
            all_routes = await fetch_bus_routes(ctx, 0)
            
            if "error" in all_routes:
                return all_routes
            
            # Filter routes by time range
            filtered_routes = []
            
            if isinstance(all_routes, list):
                for route in all_routes:
                    departure_time = route.get("departure_time", "")
                    if departure_time:
                        # Extract just the time part (HH:MM) for comparison
                        dep_time = departure_time.split(":")[0:2]  # Get hours and minutes
                        if len(dep_time) >= 2:
                            dep_hour_min = f"{dep_time[0]}:{dep_time[1]}"
                            if start_time <= dep_hour_min <= end_time:
                                filtered_routes.append(route)
            
            logger.info(f"Filtering bus routes by time range: {start_time}-{end_time}, found {len(filtered_routes)} matches")
            return {
                "start_time": start_time,
                "end_time": end_time,
                "routes": filtered_routes,
                "total_found": len(filtered_routes),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in get_routes_by_time_range: {str(e)}")
            return {"error": f"Time range filter failed: {str(e)}", "success": False}


class BusTools:
    """
    Standalone bus tools that can be used without PydanticAI agents.
    Useful for testing or direct API access.
    """
    
    @staticmethod
    async def fetch_bus_routes_direct(
        dependencies: ToolDependencies,
        route_id: int = 0
    ) -> Dict[str, Any]:
        """Direct bus route fetching without PydanticAI context."""
        base_url = f"{dependencies.base_api_url}/bus/route"
        url = f"{base_url}/{route_id}"
        
        result = await handle_http_request(dependencies.http_client, url)
        return result["data"] if result["success"] else result
    
    @staticmethod
    async def search_bus_routes_direct(
        dependencies: ToolDependencies,
        query: str
    ) -> Dict[str, Any]:
        """Direct bus route searching without PydanticAI context."""
        # Fetch all routes first
        all_routes = await BusTools.fetch_bus_routes_direct(dependencies)
        
        if "error" in all_routes:
            return all_routes
        
        # Filter routes based on the query
        query_lower = query.lower()
        filtered_routes = []
        
        if isinstance(all_routes, list):
            for route in all_routes:
                route_name = str(route.get("route_name", "")).lower()
                route_number = str(route.get("route_number", "")).lower()
                start_point = str(route.get("start_point", "")).lower()
                end_point = str(route.get("end_point", "")).lower()
                
                if (query_lower in route_name or 
                    query_lower in route_number or 
                    query_lower in start_point or 
                    query_lower in end_point):
                    filtered_routes.append(route)
        
        return {
            "query": query,
            "routes": filtered_routes,
            "total_found": len(filtered_routes),
            "success": True
        } 