#!/usr/bin/env python3
"""
Setup script for RAG system initialization.
This script loads the knowledge base and prepares the vector database.
"""
import os
import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# Set environment to load .env file
os.environ.setdefault('PYTHONPATH', str(src_path))

from src.app.services.rag_service import rag_service
from src.app.core.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main setup function."""
    logger.info("Starting RAG system setup...")
    
    # Check if knowledge base directory exists
    knowledge_base_path = Path(settings.KNOWLEDGE_BASE_PATH)
    if not knowledge_base_path.exists():
        logger.error(f"Knowledge base directory not found: {knowledge_base_path}")
        logger.info("Please ensure the knowledge_base/ directory exists with markdown files")
        return False
    
    # Check for markdown files
    md_files = list(knowledge_base_path.glob("*.md"))
    if not md_files:
        logger.error(f"No markdown files found in {knowledge_base_path}")
        logger.info("Please add some .md files to the knowledge_base/ directory")
        return False
    
    logger.info(f"Found {len(md_files)} markdown files:")
    for md_file in md_files:
        logger.info(f"  - {md_file.name}")
    
    # Check API key
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not found in environment variables")
        logger.info("Please set your OpenAI API key in the .env file")
        return False
    
    # Load the knowledge base
    logger.info("Loading knowledge base into vector database...")
    try:
        success = rag_service.load_knowledge_base(overwrite=True)
        
        if success:
            logger.info("Knowledge base loaded successfully!")
            
            # Get stats
            stats = rag_service.get_table_stats()
            logger.info(f"Statistics:")
            logger.info(f"  - Total chunks: {stats.get('total_chunks', 0)}")
            logger.info(f"  - Source files: {stats.get('unique_sources', 0)}")
            logger.info(f"  - Table name: {stats.get('table_name', 'N/A')}")
            
            # Test search
            logger.info("\nTesting search functionality...")
            test_query = "RexFlow"
            results = rag_service.search_knowledge(test_query, limit=3)
            
            if results:
                logger.info(f"Search test successful! Found {len(results)} results for '{test_query}'")
                for i, result in enumerate(results[:2], 1):
                    score = result.get('_relevance_score', 0)
                    source = result.get('source_file', 'unknown')
                    logger.info(f"  {i}. Source: {source}, Score: {score:.3f}")
            else:
                logger.warning(f"Search test returned no results for '{test_query}'")
            
            logger.info("\n✅ RAG system setup completed successfully!")
            logger.info("You can now use the knowledge base search functionality in your agent.")
            return True
            
        else:
            logger.error("Failed to load knowledge base")
            return False
            
    except Exception as e:
        logger.error(f"Error during setup: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)