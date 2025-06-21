import logfire
import time
from typing import List, Dict, Any

from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
import lancedb
from lancedb_setup import setup_lancedb, retrive_similar_docs
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


logfire.configure()
Agent.instrument_all()


class OptimizedRAGSystem:
    """Optimized RAG system with reduced latency"""
    
    def __init__(self):
        # Initialize database connection once
        self.db_path = "./db"
        self.table_name = "mknowledge"
        self.db = lancedb.connect(self.db_path)
        
        # Initialize table once
        self.knowledge_table = (
            self.db.open_table(self.table_name) 
            if self.table_name in self.db.table_names() 
            else setup_lancedb()
        )
        
        # Initialize agent once
        self.agent = self._setup_unified_agent()
        
        # Configuration
        self.max_docs = 15  # Reduced from 100
        self.similarity_threshold = 0.7
        self.max_context_length = 4000  # Limit context size
        
    def _setup_unified_agent(self):
        """Setup a single unified agent that handles both query processing and response generation"""
        system_prompt = """You are a helpful AI assistant with access to a knowledge base.

When answering questions:
1. Use the provided context to answer the user's question
2. If the context doesn't contain relevant information, say so clearly
3. Be concise but comprehensive
4. Cite information when possible
5. If you need to search for specific information, you can rephrase the search internally

Answer based on the provided context and your general knowledge."""
        
        agent = Agent(
            model="groq:llama-3.3-70b-versatile",
            name="Unified RAG Agent",
            system_prompt=system_prompt,
        )
        return agent
        
    def _optimize_document_retrieval(self, query: str) -> List[Dict[str, Any]]:
        """Optimized document retrieval with smart filtering"""
        try:
            # Use faster vector search without heavy reranking for initial retrieval
            results = (
                self.knowledge_table.search(query, query_type="vector")
                .limit(self.max_docs)
                .to_list()
            )
            
            # Filter by similarity threshold
            filtered_results = [
                doc for doc in results 
                if doc.get("_relevance_score", 0) >= self.similarity_threshold
            ]
            
            return filtered_results[:10]  # Top 10 most relevant
            
        except Exception as e:
            print(f"Error in document retrieval: {e}")
            return []
    
    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        """Efficiently build context from documents"""
        if not docs:
            return ""
        
        # Use list comprehension and join for efficient string building
        context_parts = []
        current_length = 0
        
        for doc in docs:
            text = doc.get("text", "")
            # Truncate if adding this doc would exceed max context length
            if current_length + len(text) > self.max_context_length:
                remaining_space = self.max_context_length - current_length
                if remaining_space > 100:  # Only add if meaningful space left
                    text = text[:remaining_space] + "..."
                    context_parts.append(text)
                break
            
            context_parts.append(text)
            current_length += len(text)
        
        return "\n\n".join(context_parts)
    
    def query(self, user_query: str, message_history=None) -> str:
        """Process a query with optimized performance"""
        start_time = time.time()
        
        # Step 1: Retrieve relevant documents (optimized)
        retrieved_docs = self._optimize_document_retrieval(user_query)
        retrieval_time = time.time()
        
        # Step 2: Build context efficiently
        knowledge_context = self._build_context(retrieved_docs)
        context_time = time.time()
        
        # Step 3: Single agent call with combined prompt
        if knowledge_context:
            prompt = f"""Context from knowledge base:
{knowledge_context}

User Question: {user_query}

Please answer the question based on the provided context. If the context doesn't contain relevant information, please say so clearly."""
        else:
            prompt = f"""No specific context found in knowledge base for this query.

User Question: {user_query}

Please provide a helpful answer based on your general knowledge."""
        
        # Single agent call
        response = self.agent.run_sync(prompt, message_history=message_history)
        end_time = time.time()
        
        # Performance logging
        print(f"Performance metrics:")
        print(f"  - Document retrieval: {retrieval_time - start_time:.2f}s")
        print(f"  - Context building: {context_time - retrieval_time:.2f}s") 
        print(f"  - LLM generation: {end_time - context_time:.2f}s")
        print(f"  - Total time: {end_time - start_time:.2f}s")
        print(f"  - Documents used: {len(retrieved_docs)}")
        
        return response


def setup_knowledge_query_agent():
    """
    Setup Knowledge Query agent (DEPRECATED - keeping for compatibility)
    """
    agent = Agent(
        "groq:llama-3.3-70b-versatile",
        name="Knowledge Query Agent",
        deps_type=str,
        output_type=str,
        system_prompt=(
            "You are a query‐generation assistant. "
            "Every time the user gives a text string, you must:\n"
            "  1. Understand the user's intent.\n"
            "  2. Rephrase it as a concise, grammatically correct question\n"
            "     suitable for passing to a knowledge base.\n"
            "  3. Preserve meaning but correct any grammar or tense issues.\n"
            "Do not add information that was not in the user's text."
        ),
    )
    return agent


def setup_main_agent():
    """
    Setup the main agent (DEPRECATED - keeping for compatibility)
    """
    agent = Agent(
        name="Main Agent",
        model="groq:llama-3.3-70b-versatile",
        system_prompt="You are a helpful assistant",
    )
    return agent


def main():
    """
    Main execution flow - OPTIMIZED VERSION
    """
    print("Initializing Optimized RAG System...")
    rag_system = OptimizedRAGSystem()
    print("System ready!")
    
    message_history = None
    
    while True:
        query = input("\nEnter your query: ")
        if query.lower() in ["exit", "quit"]:
            break
            
        print(f"\nProcessing: {query}")
        response = rag_system.query(query, message_history)
        print(f"\nResponse: {response.output}")
        
        # Update message history
        message_history = response.all_messages()


def main_legacy():
    """
    Legacy main execution flow (SLOW VERSION - for comparison)
    """
    print("Using LEGACY (slow) implementation...")
    
    db_path = "./db"
    table_name = "mknowledge"
    db = lancedb.connect(db_path)

    knowledge_table = db.open_table(table_name) if table_name in db.table_names() else setup_lancedb()
    knowledge_query_agent = setup_knowledge_query_agent()
    agent = setup_main_agent()

    message_history = None

    while True:
        query = input("Enter your query: ")
        if query == "exit":
            break
            
        start_time = time.time()
        
        # First agent call - query reformulation
        res = knowledge_query_agent.run_sync(query)
        knowledge_query = res.output
        print("Knowledge Query : ", knowledge_query)
        
        # Document retrieval
        retrieved_docs = retrive_similar_docs(
            knowledge_table, knowledge_query, limit=100
        )
        
        # Context building
        knowledge_context = ""
        for doc in retrieved_docs:
            if doc["_relevance_score"] > 0.7:
                knowledge_context += doc["text"]

        # Second agent call - final response
        prompt = f"Context: \n{knowledge_context}\n\nUser Query: \n{query}\n\nAnswer based on the above context: "
        response = agent.run_sync(prompt, message_history=message_history)
        
        end_time = time.time()
        print(f"Total time: {end_time - start_time:.2f}s")
        print(response.output)

        message_history = response.all_messages()


if __name__ == "__main__":
    # Run optimized version by default
    main()
    
    # Uncomment to run legacy version for comparison
    # main_legacy()
