"""
Cafeteria-related tools for PydanticAI agents.

These tools can be used by any agent that needs to fetch cafeteria menu data.
"""

from typing import Dict, Any, Optional
from pydantic_ai import Agent, RunContext
from src.app.agents.tools.base import ToolDependencies, handle_http_request
import logging

logger = logging.getLogger(__name__)


def register_cafeteria_tools(agent: Agent, deps_type: type) -> None:
    """
    Register cafeteria-related tools with a PydanticAI agent.

    Args:
        agent: The PydanticAI agent to register tools with
        deps_type: The dependencies type that should include ToolDependencies
    """

    @agent.tool
    async def fetch_cafeteria_menu(
        ctx: RunContext, cafeteria_id: int = 0
    ) -> Dict[str, Any]:
        """
        Fetch cafeteria menu data from the campus cafeteria API.

        Args:
            cafeteria_id: Cafeteria ID to fetch menu for, defaults to 0 for main cafeteria

        Returns:
            Cafeteria menu data from the API
        """
        try:
            url = f"{ctx.deps.base_api_url}/cafeteria/menu/{cafeteria_id}"

            # Use common HTTP handler
            result = await handle_http_request(ctx.deps.http_client, url)

            if result["success"]:
                menu_data = result["data"]
                logger.info(
                    f"Successfully fetched cafeteria menu data for cafeteria {cafeteria_id}"
                )
                return menu_data
            else:
                return result

        except Exception as e:
            logger.error(f"Unexpected error in fetch_cafeteria_menu: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    @agent.tool
    async def search_menu_items(
        ctx: RunContext, query: str, cafeteria_id: int = 0
    ) -> Dict[str, Any]:
        """
        Search for specific menu items by name or category.

        Args:
            query: Search query for menu items (name, ingredient, or category)
            cafeteria_id: Cafeteria ID to search in, defaults to 0 for main cafeteria

        Returns:
            Filtered menu data matching the query
        """
        try:
            # First fetch the cafeteria menu
            menu_data = await fetch_cafeteria_menu(ctx, cafeteria_id)

            if "error" in menu_data:
                return menu_data

            # Determine the structure of the response and filter menu items
            filtered_items = []
            query_lower = query.lower()

            # Handle different possible response structures
            menu_items = []
            if isinstance(menu_data, list):
                menu_items = menu_data
            elif isinstance(menu_data, dict):
                if "menu" in menu_data:
                    menu_items = menu_data["menu"]
                elif "items" in menu_data:
                    menu_items = menu_data["items"]
                elif "meals" in menu_data:
                    menu_items = menu_data["meals"]
                else:
                    # Try to extract items from nested structure
                    for key, value in menu_data.items():
                        if isinstance(value, list):
                            menu_items.extend(value)

            # Filter menu items based on query
            for item in menu_items:
                if isinstance(item, dict):
                    name = item.get("name", "").lower()
                    description = item.get("description", "").lower()
                    category = item.get("category", "").lower()
                    ingredients = str(item.get("ingredients", "")).lower()

                    if (
                        query_lower in name
                        or query_lower in description
                        or query_lower in category
                        or query_lower in ingredients
                    ):
                        filtered_items.append(item)
                elif isinstance(item, str) and query_lower in item.lower():
                    filtered_items.append({"name": item})

            logger.info(
                f"Searching menu items with query: '{query}', found {len(filtered_items)} matches"
            )
            return {
                "query": query,
                "cafeteria_id": cafeteria_id,
                "menu_items": filtered_items,
                "total_count": len(filtered_items),
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error in search_menu_items: {str(e)}")
            return {"error": f"Menu search failed: {str(e)}", "success": False}


class CafeteriaTools:
    """
    Standalone cafeteria tools that can be used without PydanticAI agents.
    Useful for testing or direct API access.
    """

    @staticmethod
    async def fetch_cafeteria_menu_direct(
        dependencies: ToolDependencies, cafeteria_id: int = 0
    ) -> Dict[str, Any]:
        """Direct cafeteria menu fetching without PydanticAI context."""
        url = f"{dependencies.base_api_url}/cafeteria/menu/{cafeteria_id}"

        result = await handle_http_request(dependencies.http_client, url)
        return result["data"] if result["success"] else result

    @staticmethod
    async def search_menu_items_direct(
        dependencies: ToolDependencies, query: str, cafeteria_id: int = 0
    ) -> Dict[str, Any]:
        """Direct menu item searching without PydanticAI context."""
        # Fetch cafeteria menu first
        menu_data = await CafeteriaTools.fetch_cafeteria_menu_direct(
            dependencies, cafeteria_id
        )

        if "error" in menu_data:
            return menu_data

        # Apply the same filtering logic as the agent tool
        filtered_items = []
        query_lower = query.lower()

        # Handle different possible response structures
        menu_items = []
        if isinstance(menu_data, list):
            menu_items = menu_data
        elif isinstance(menu_data, dict):
            if "menu" in menu_data:
                menu_items = menu_data["menu"]
            elif "items" in menu_data:
                menu_items = menu_data["items"]
            elif "meals" in menu_data:
                menu_items = menu_data["meals"]
            else:
                # Try to extract items from nested structure
                for key, value in menu_data.items():
                    if isinstance(value, list):
                        menu_items.extend(value)

        # Filter menu items based on query
        for item in menu_items:
            if isinstance(item, dict):
                name = item.get("name", "").lower()
                description = item.get("description", "").lower()
                category = item.get("category", "").lower()
                ingredients = str(item.get("ingredients", "")).lower()

                if (
                    query_lower in name
                    or query_lower in description
                    or query_lower in category
                    or query_lower in ingredients
                ):
                    filtered_items.append(item)
            elif isinstance(item, str) and query_lower in item.lower():
                filtered_items.append({"name": item})

        return {
            "query": query,
            "cafeteria_id": cafeteria_id,
            "menu_items": filtered_items,
            "total_count": len(filtered_items),
            "success": True,
        }
