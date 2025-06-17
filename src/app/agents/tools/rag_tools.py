from typing import Optional, List, Dict, Any
from pydantic_ai import Tool, RunContext
from pydantic import BaseModel, Field
import logging

from src.app.agents.tools.base import ToolDependencies
from src.app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class KnowledgeSearchRequest(BaseModel):
    """Request model for knowledge search."""
    query: str = Field(..., description="The search query to find relevant knowledge")
    max_results: Optional[int] = Field(
        default=5, description="Maximum number of results to return"
    )
    search_type: Optional[str] = Field(
        default="hybrid", description="Type of search: 'hybrid', 'vector', or 'fts'"
    )


class KnowledgeSearchResponse(BaseModel):
    """Response model for knowledge search."""
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    context: str = Field(..., description="Combined context from all results")
    total_results: int = Field(..., description="Total number of results found")
    query: str = Field(..., description="Original search query")


class KnowledgeStatusResponse(BaseModel):
    """Response model for knowledge base status."""
    loaded: bool = Field(..., description="Whether knowledge base is loaded")
    total_chunks: Optional[int] = Field(None, description="Total number of document chunks")
    unique_sources: Optional[int] = Field(None, description="Number of unique source files")
    table_name: Optional[str] = Field(None, description="Name of the vector database table")
    error: Optional[str] = Field(None, description="Error message if any")


async def search_knowledge_base(
    deps: ToolDependencies, request: KnowledgeSearchRequest
) -> KnowledgeSearchResponse:
    """
    Search the knowledge base for relevant information.
    
    This tool searches through all loaded knowledge documents using vector similarity
    and returns the most relevant information based on the query.
    """
    try:
        logger.info(f"Searching knowledge base for: {request.query}")
        
        # Perform the search
        results = rag_service.search_knowledge(
            query=request.query,
            query_type=request.search_type,
            limit=request.max_results
        )
        
        # Get combined context
        context = rag_service.get_context_from_results(results)
        
        return KnowledgeSearchResponse(
            results=results,
            context=context,
            total_results=len(results),
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return KnowledgeSearchResponse(
            results=[],
            context="",
            total_results=0,
            query=request.query
        )


async def get_knowledge_base_status(deps: ToolDependencies) -> KnowledgeStatusResponse:
    """
    Get the current status of the knowledge base.
    
    This tool returns information about whether the knowledge base is loaded
    and provides statistics about the stored documents.
    """
    try:
        stats = rag_service.get_table_stats()
        
        return KnowledgeStatusResponse(
            loaded=stats.get("loaded", False),
            total_chunks=stats.get("total_chunks"),
            unique_sources=stats.get("unique_sources"),
            table_name=stats.get("table_name"),
            error=stats.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error getting knowledge base status: {e}")
        return KnowledgeStatusResponse(
            loaded=False,
            error=str(e)
        )


async def load_knowledge_base(
    deps: ToolDependencies, overwrite: bool = False
) -> Dict[str, Any]:
    """
    Load or reload the knowledge base from markdown files.
    
    This tool processes all markdown files in the knowledge_base directory
    and loads them into the vector database for searching.
    """
    try:
        logger.info(f"Loading knowledge base (overwrite={overwrite})")
        
        success = rag_service.load_knowledge_base(overwrite=overwrite)
        
        if success:
            stats = rag_service.get_table_stats()
            return {
                "success": True,
                "message": "Knowledge base loaded successfully",
                "stats": stats
            }
        else:
            return {
                "success": False,
                "message": "Failed to load knowledge base",
                "stats": {}
            }
            
    except Exception as e:
        logger.error(f"Error loading knowledge base: {e}")
        return {
            "success": False,
            "message": f"Error loading knowledge base: {str(e)}",
            "stats": {}
        }


def register_rag_tools(agent, deps_type):
    """Register RAG tools with the agent."""
    
    @agent.tool
    async def search_knowledge(
        ctx: RunContext, 
        query: str,
        max_results: int = 5,
        search_type: str = "hybrid"
    ) -> str:
        """
        Search the knowledge base for information relevant to the user's query.
        
        Args:
            query: The search query to find relevant knowledge
            max_results: Maximum number of results to return (default: 5)
            search_type: Type of search - 'hybrid' (recommended), 'vector', or 'fts'
            
        Returns:
            A formatted string with relevant information from the knowledge base
        """
        try:
            # Create request
            request = KnowledgeSearchRequest(
                query=query,
                max_results=max_results,
                search_type=search_type
            )
            
            # Perform search
            response = await search_knowledge_base(ctx.deps, request)
            
            if response.total_results == 0:
                return f"No relevant information found in the knowledge base for: {query}"
            
            # Format the response
            formatted_response = f"Found {response.total_results} relevant results for '{query}':\n\n"
            formatted_response += response.context
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error in search_knowledge tool: {e}")
            return f"Error searching knowledge base: {str(e)}"
    
    @agent.tool
    async def check_knowledge_status(ctx: RunContext) -> str:
        """
        Check the current status of the knowledge base.
        
        Returns:
            Information about whether the knowledge base is loaded and its statistics
        """
        try:
            response = await get_knowledge_base_status(ctx.deps)
            
            if not response.loaded:
                return "Knowledge base is not loaded. Please load it first to search for information."
            
            status_info = f"Knowledge base status:\n"
            status_info += f"- Loaded: {response.loaded}\n"
            status_info += f"- Total document chunks: {response.total_chunks}\n"
            status_info += f"- Unique source files: {response.unique_sources}\n"
            status_info += f"- Table name: {response.table_name}\n"
            
            return status_info
            
        except Exception as e:
            logger.error(f"Error in check_knowledge_status tool: {e}")
            return f"Error checking knowledge base status: {str(e)}"
    
    @agent.tool
    async def initialize_knowledge_base(ctx: RunContext, overwrite: bool = False) -> str:
        """
        Initialize or reload the knowledge base from markdown files.
        
        Args:
            overwrite: Whether to overwrite existing knowledge base (default: False)
            
        Returns:
            Status message about the loading process
        """
        try:
            result = await load_knowledge_base(ctx.deps, overwrite=overwrite)
            
            if result["success"]:
                stats = result["stats"]
                message = f"Knowledge base loaded successfully!\n"
                message += f"- Total chunks: {stats.get('total_chunks', 0)}\n"
                message += f"- Source files: {stats.get('unique_sources', 0)}\n"
                return message
            else:
                return f"Failed to load knowledge base: {result['message']}"
                
        except Exception as e:
            logger.error(f"Error in initialize_knowledge_base tool: {e}")
            return f"Error initializing knowledge base: {str(e)}"

    logger.info("RAG tools registered successfully") 