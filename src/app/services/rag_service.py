"""
RAG (Retrieval-Augmented Generation) service for knowledge base management.

This module provides functionality to load, chunk, and search documents in a
LanceDB vector database for enhanced AI responses with domain-specific knowledge.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Any, Optional

import lancedb
import tiktoken
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector
from lancedb.rerankers import LinearCombinationReranker
from lancedb.table import LanceTable

from src.app.core.config.settings import settings

logger = logging.getLogger(__name__)


def get_embedding_function():
    """Get the embedding function for the current setup."""
    registry = get_registry()
    return registry.get("openai").create(name=settings.EMBEDDING_MODEL)


# Create embedding function instance
embedding_func = get_embedding_function()


class Document(LanceModel):
    """Schema for knowledge base documents."""

    id: str
    text: str = embedding_func.SourceField()
    vector: Vector(embedding_func.ndims()) = embedding_func.VectorField()
    source_file: str
    chunk_index: int
    file_path: str
    file_size: int
    total_chunks: int


class RAGService:
    """Service for managing RAG operations with LanceDB."""

    def __init__(self):
        self.db_path = settings.VECTOR_DB_PATH
        self.table_name = settings.RAG_TABLE_NAME
        self.knowledge_base_path = settings.KNOWLEDGE_BASE_PATH
        self.chunk_size = settings.RAG_CHUNK_SIZE
        self.similarity_threshold = settings.RAG_SIMILARITY_THRESHOLD
        self.max_results = settings.RAG_MAX_RESULTS
        self.embedding_func = embedding_func

        # Ensure vector database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def chunk_text(self, text: str, encoding_name: str = "cl100k_base") -> List[str]:
        """Chunk text into smaller parts based on token count."""
        try:
            encoding = tiktoken.get_encoding(encoding_name)
            tokens = encoding.encode(text)

            chunks = []
            for i in range(0, len(tokens), self.chunk_size):
                chunk_tokens = tokens[i : i + self.chunk_size]
                chunk_text = encoding.decode(chunk_tokens)
                chunks.append(chunk_text)

            return chunks
        except Exception as e:
            logger.error("Error chunking text: %s", e)
            return [text]  # Return original text if chunking fails

    def get_or_create_table(self, overwrite: bool = False) -> LanceTable:
        """Get existing table or create a new one."""
        try:
            db = lancedb.connect(self.db_path)

            # Check if table exists
            existing_tables = db.table_names()

            if self.table_name in existing_tables and not overwrite:
                logger.info("Using existing table: %s", self.table_name)
                return db.open_table(self.table_name)

            # Create new table
            mode = "overwrite" if overwrite else "create"
            table = db.create_table(self.table_name, schema=Document, mode=mode)

            # Create full-text search index
            table.create_fts_index("text", replace=overwrite)

            logger.info("Created new table: %s", self.table_name)
            return table

        except Exception as e:
            logger.error("Error creating/getting table: %s", e)
            raise

    def load_knowledge_base(self, overwrite: bool = False) -> bool:
        """Load all markdown files from knowledge base into vector database."""
        try:
            knowledge_base_dir = Path(self.knowledge_base_path)

            if not knowledge_base_dir.exists():
                logger.error(
                    "Knowledge base directory not found: %s", knowledge_base_dir
                )
                return False

            # Get all markdown files
            md_files = list(knowledge_base_dir.glob("*.md"))

            if not md_files:
                logger.warning("No markdown files found in %s", knowledge_base_dir)
                return False

            logger.info("Found %d markdown files to process", len(md_files))

            # Get or create table
            table = self.get_or_create_table(overwrite=overwrite)
            all_documents = self._process_markdown_files(md_files)

            if all_documents:
                self._add_documents_to_table(table, all_documents, len(md_files))
                return True

            logger.warning("No documents were processed successfully")
            return False

        except Exception as e:
            logger.error("Error loading knowledge base: %s", e)
            return False

    def _process_markdown_files(self, md_files: List[Path]) -> List[Dict[str, Any]]:
        """Process markdown files and return document chunks."""
        all_documents = []

        for md_file in md_files:
            logger.info("Processing file: %s", md_file.name)

            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Chunk the content
                chunks = self.chunk_text(content)

                # Create document entries for each chunk
                for i, chunk in enumerate(chunks):
                    doc_id = f"{md_file.stem}_chunk_{i}"
                    document = {
                        "id": doc_id,
                        "text": chunk,
                        "source_file": md_file.name,
                        "chunk_index": i,
                        "file_path": str(md_file),
                        "file_size": len(content),
                        "total_chunks": len(chunks),
                    }
                    all_documents.append(document)

            except Exception as e:
                logger.error("Error processing file %s: %s", md_file.name, e)
                continue

        return all_documents

    def _add_documents_to_table(
        self, table: LanceTable, documents: List[Dict[str, Any]], file_count: int
    ):
        """Add documents to table in batches."""
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            table.add(batch)
            logger.info(
                "Added batch %d (%d documents)", i // batch_size + 1, len(batch)
            )

        logger.info(
            "Successfully loaded %d document chunks from %d files",
            len(documents),
            file_count,
        )

    def search_knowledge(
        self,
        query: str,
        query_type: str = "hybrid",
        limit: Optional[int] = None,
        reranker_weight: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search for relevant documents in the knowledge base."""
        try:
            # Get table
            db = lancedb.connect(self.db_path)

            if self.table_name not in db.table_names():
                logger.warning(
                    "Knowledge base table not found. Please load knowledge base first."
                )
                return []

            table = db.open_table(self.table_name)

            # Set limit
            search_limit = limit or self.max_results

            # Perform search with reranking
            reranker = LinearCombinationReranker(weight=reranker_weight)
            results = (
                table.search(query, query_type=query_type)
                .rerank(reranker=reranker)
                .limit(search_limit)
                .to_list()
            )

            # Filter by similarity threshold
            filtered_results = [
                result
                for result in results
                if result.get("_relevance_score", 0) >= self.similarity_threshold
            ]

            logger.info(
                "Found %d relevant documents for query: %s...",
                len(filtered_results),
                query[:50],
            )
            return filtered_results

        except Exception as e:
            logger.error("Error searching knowledge base: %s", e)
            return []

    def get_context_from_results(self, results: List[Dict[str, Any]]) -> str:
        """Extract and combine text context from search results."""
        if not results:
            return ""

        context_parts = []
        for result in results:
            text = result.get("text", "")
            source = result.get("source_file", "unknown")
            score = result.get("_relevance_score", 0)

            # Add source information
            context_parts.append(f"[Source: {source} (Relevance: {score:.2f})]")
            context_parts.append(text)
            context_parts.append("---")

        return "\n".join(context_parts)

    def is_knowledge_base_loaded(self) -> bool:
        """Check if knowledge base is loaded in the vector database."""
        try:
            db = lancedb.connect(self.db_path)
            return self.table_name in db.table_names()
        except Exception:
            return False

    def get_table_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base table."""
        try:
            if not self.is_knowledge_base_loaded():
                return {"error": "Knowledge base not loaded"}

            db = lancedb.connect(self.db_path)
            table = db.open_table(self.table_name)

            # Get basic stats
            stats = {
                "total_documents": len(table),
                "table_name": self.table_name,
                "db_path": self.db_path,
                "chunk_size": self.chunk_size,
                "similarity_threshold": self.similarity_threshold,
                "max_results": self.max_results,
            }

            return stats

        except Exception as e:
            logger.error("Error getting table stats: %s", e)
            return {"error": str(e)}


@lru_cache()
def get_rag_service() -> RAGService:
    """Get singleton RAG service instance."""
    return RAGService()


# Initialize the service
rag_service = get_rag_service()
