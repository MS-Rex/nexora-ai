"""
Department-related tools for PydanticAI agents.

These tools can be used by any agent that needs to fetch or search department data.
"""

from typing import Dict, Any, Optional
from pydantic_ai import Agent, RunContext
from src.app.agents.tools.base import ToolDependencies, handle_http_request
import logging

logger = logging.getLogger(__name__)


def register_department_tools(agent: Agent, deps_type: type) -> None:
    """
    Register department-related tools with a PydanticAI agent.
    
    Args:
        agent: The PydanticAI agent to register tools with
        deps_type: The dependencies type that should include ToolDependencies
    """
    
    @agent.tool
    async def fetch_departments(ctx: RunContext, department_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch department data from the campus departments API.
        
        Args:
            department_id: Optional department ID to fetch specific department, 
                         if not provided, fetches all departments
            
        Returns:
            Department data from the API
        """
        try:
            # Build URL based on whether specific department is requested
            if department_id is not None:
                url = f"{ctx.deps.base_api_url}/department/data/{department_id}"
            else:
                url = f"{ctx.deps.base_api_url}/department/data/0"
                
            # Use common HTTP handler
            result = await handle_http_request(ctx.deps.http_client, url)
            
            if result["success"]:
                return result["data"]
            else:
                return result
                
        except Exception as e:
            logger.error(f"Unexpected error in fetch_departments: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    @agent.tool
    async def search_departments(ctx: RunContext, query: str) -> Dict[str, Any]:
        """
        Search for departments by name or description keyword.
        
        Args:
            query: Search query for departments (name or description keywords)
            
        Returns:
            Filtered departments data matching the query
        """
        try:
            # First fetch all departments using the other tool
            all_departments_result = await fetch_departments(ctx)
            
            if "error" in all_departments_result:
                return all_departments_result
            
            # Determine the structure of the response
            if isinstance(all_departments_result, list):
                departments_list = all_departments_result
            elif isinstance(all_departments_result, dict):
                if "departments" in all_departments_result:
                    departments_list = all_departments_result["departments"]
                else:
                    # Assume the dict itself is a single department
                    departments_list = [all_departments_result]
            else:
                departments_list = []
            
            # Filter departments based on query
            filtered_departments = []
            query_lower = query.lower()
            
            for dept in departments_list:
                if isinstance(dept, dict):
                    name = dept.get("name", "").lower()
                    description = dept.get("description", "").lower()
                    if query_lower in name or query_lower in description:
                        filtered_departments.append(dept)
            
            logger.info(f"Searching departments with query: '{query}', found {len(filtered_departments)} matches")
            return {
                "query": query,
                "departments": filtered_departments,
                "total_count": len(filtered_departments),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in search_departments: {str(e)}")
            return {"error": f"Search failed: {str(e)}", "success": False}


class DepartmentTools:
    """
    Standalone department tools that can be used without PydanticAI agents.
    Useful for testing or direct API access.
    """
    
    @staticmethod
    async def fetch_departments_direct(
        dependencies: ToolDependencies, 
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Direct department fetching without PydanticAI context."""
        if department_id is not None:
            url = f"{dependencies.base_api_url}/department/data/{department_id}"
        else:
            url = f"{dependencies.base_api_url}/department/data/0"
        
        result = await handle_http_request(dependencies.http_client, url)
        return result["data"] if result["success"] else result
    
    @staticmethod
    async def search_departments_direct(
        dependencies: ToolDependencies,
        query: str
    ) -> Dict[str, Any]:
        """Direct department searching without PydanticAI context."""
        # Fetch all departments first
        all_departments = await DepartmentTools.fetch_departments_direct(dependencies)
        
        if "error" in all_departments:
            return all_departments
        
        # Apply the same filtering logic
        departments_list = all_departments if isinstance(all_departments, list) else [all_departments]
        filtered_departments = []
        query_lower = query.lower()
        
        for dept in departments_list:
            if isinstance(dept, dict):
                name = dept.get("name", "").lower()
                description = dept.get("description", "").lower()
                if query_lower in name or query_lower in description:
                    filtered_departments.append(dept)
        
        return {
            "query": query,
            "departments": filtered_departments,
            "total_count": len(filtered_departments),
            "success": True
        } 