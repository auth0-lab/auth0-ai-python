"""
Langchain Example: Retrievers with Okta FGA (Fine-Grained Authorization)

It performs the following steps:
   1. Defines a user ID.
   2. Reads documents from a data source.
   3. Creates a MemoryStore from the documents.
   4. Sets up a RetrievalChain with an FGARetriever to enforce permissions.
   5. Executes a query and logs the response.

The FGARetriever checks if the user has the "viewer" relation to the document
based on predefined tuples in Okta FGA.

Example:
- A tuple {user: "user:*", relation: "viewer", object: "doc:public-doc"} allows all users to view "public-doc".
- A tuple {user: "user:user1", relation: "viewer", object: "doc:private-doc"} allows "user1" to view "private-doc".

The output of the query depends on the user's permissions to view the documents.
"""

from auth0_ai_langchain import FGARetriever
from dotenv import load_dotenv
from .memory_store import MemoryStore
from openfga_sdk.client.models import ClientBatchCheckItem
from .read_documents import read_documents
from .retrieval_chain import RetrievalChain
from termcolor import colored

load_dotenv()

def query(user: str, question: str):
    print(colored(f"{user}: {question}", "blue"))

    # UserID
    user_id = user
    documents = read_documents()
    vector_store = MemoryStore.from_documents(documents)
    retrieval_chain = RetrievalChain.create(
        # Decorate the retriever with the FGARetriever to check the permissions.
        retriever=FGARetriever(
            retriever=vector_store.as_retriever(),
            build_query=lambda doc: ClientBatchCheckItem(
                user=f"user:{user_id}",
                object=f"doc:{doc.metadata.get('id')}",
                relation="viewer",
            ),
        )
    )

    print(f"answer: {retrieval_chain.query(question).get('answer')}\n")


def main():
    print("..:: Langchain RAG with FGA demo ::..\n")
    question = """what is the forecast for ZEKO?"""
    print("--------------------------")

    # `user0` only have access to public docs only.
    query("user0", question)

    print("--------------------------")

    # `user1` has access to public and private docs.
    query("user1", question)


if __name__ == "__main__":
    main()
