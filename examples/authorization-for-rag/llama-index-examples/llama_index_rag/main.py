import logging
from dotenv import load_dotenv
from termcolor import colored
from .retriever import create_retriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.openai import OpenAI

load_dotenv()

def query(user: str, question: str):
    print(colored(f"{user}: {question}", "blue"))
    retriever = create_retriever(user)

    query_engine = RetrieverQueryEngine.from_args(
        retriever=retriever,
        llm=OpenAI(
            model="gpt-4o-mini",
            system_prompt="Answer the user's question based on the information you already have. If you don't have enough information, just say so.",
        ),
    )

    response = query_engine.query("What is the forecast for ZEKO?")
    print(response)

def main():
    openai_logger = logging.getLogger("openai")
    openai_logger.setLevel(logging.DEBUG)

    print("llama_index RAG with FGA demo")
    question = """what is the forecast for ZEKO?"""

    # `user0` only have access to public docs only.
    print("--------------------------")
    query("user0", question)

    # `user1` has access to public and private docs.
    print("--------------------------")
    query("user1", question)

if __name__ == "__main__":
    main()
