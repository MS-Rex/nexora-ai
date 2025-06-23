import logfire

from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
import lancedb
from lancedb_setup import setup_lancedb, retrive_similar_docs
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


logfire.configure()
Agent.instrument_all()

# class Settings(BaseSettings):
#     # groq_api_key: str
#     # openai_api_key: str
#     # weatherstack_api_key: str
#     model_config = SettingsConfigDict(env_file='.env',extra="allow")

# @lru_cache
# def get_settings()->Settings:
#     print("Get settings called")
#     return Settings()

# settings= get_settings()
# print(settings.groq_api_key)


# agent = Agent(
#     "groq:deepseek-r1-distill-llama-70b",
#     tools=[duckduckgo_search_tool()],
#     system_prompt="Search DuckDuckGo for the given query and return the results.",
#     instrument=True,
# )

# result = agent.run_sync("Give me top 5 trending English Songs?")
# print(result.output)


def setup_knowledge_query_agent():
    """
    Setup Knowledge Query agent
    """
    agent = Agent(
        "groq:llama-3.3-70b-versatile",
        name="Knowledge Query Agent",
        # model="groq:deepseek-r1-distill-llama-70b",
        deps_type=str,
        output_type=str,
        # system_prompt="From the input text string,please generate a query string to pass to the knowledge base.",
        system_prompt=(
            "You are a query‐generation assistant. "
            "Every time the user gives a text string, you must:\n"
            "  1. Understand the user’s intent.\n"
            "  2. Rephrase it as a concise, grammatically correct question\n"
            "     suitable for passing to a knowledge base.\n"
            "  3. Preserve meaning but correct any grammar or tense issues.\n"
            "Do not add information that was not in the user’s text."
        ),
    )
    return agent


def setup_main_agent():
    """
    Setup the main agent
    """
    agent = Agent(
        name="Main Agent",
        model="groq:llama-3.3-70b-versatile",
        system_prompt="You are a helpful assistant",
    )
    return agent


def main():
    """
    Main execution flow of the App
    """
    db_path = "./db"
    table_name = "mknowledge"
    db = lancedb.connect(db_path)

    knowledge_table = db.open_table(table_name) if db.table_names() else setup_lancedb()
    knowledge_query_agent = setup_knowledge_query_agent()
    agent = setup_main_agent()

    message_history = None

    while True:
        query = input("Enter your query: ")
        if query == "exit":
            break
        res = knowledge_query_agent.run_sync(query)
        knowledge_query = res.output
        print("Knowledge Query : ", knowledge_query)
        retrieved_docs = retrive_similar_docs(
            knowledge_table, knowledge_query, limit=100
        )
        knowledge_context = ""
        for doc in retrieved_docs:
            if doc["_relevance_score"] > 0.7:
                knowledge_context += doc["text"]

        prompt = f"Context: \n{knowledge_context}\n\nUser Query: \n{query}\n\nAnswer based on the above context: "
        response = agent.run_sync(prompt, message_history=message_history)
        print(response.output)

        message_history = response.all_messages()


main()
