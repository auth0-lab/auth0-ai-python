# Auth0 AI for LangChain

`langchain-auth0-ai` is an SDK for building secure AI-powered applications using [Auth0](https://www.auth0.ai/), [Okta FGA](https://docs.fga.dev/) and [LangChain](https://python.langchain.com/docs/tutorials/).

## Installation

> [!WARNING]
> `langchain-auth0-ai` is currently under development and it is not intended to be used in production, and therefore has no official support.

```bash
pip install langchain-auth0-ai
```

## RAG with FGA

Example [RAG Application](../../examples/authorization-for-rag/langchain-examples/).

Create a retriever instance using the `FGARetriever` class.

```python
from langchain.vectorstores import VectorStoreIndex
from langchain.schema import Document
from langchain_auth0_ai import FGARetriever
from openfga_sdk.client.models import ClientCheckRequest
from openfga_sdk import ClientConfiguration
from openfga_sdk.credentials import CredentialConfiguration, Credentials

# Define some docs:
documents = [
    Document(page_content="This is a public doc", metadata={"doc_id": "public-doc"}),
    Document(page_content="This is a private doc", metadata={"doc_id": "private-doc"}),
]

# Create a vector store:
vector_store = VectorStoreIndex.from_documents(documents)

# Create a retriever:
base_retriever = vector_store.as_retriever()

# Create the FGA retriever wrapper:
retriever = FGARetriever(
    base_retriever,
    build_query=lambda node: ClientCheckRequest(
        user=f'user:{user}',
        object=f'doc:{node.metadata["doc_id"]}',
        relation="viewer",
    )
)

# Create a query engine:
query_engine = RetrieverQueryEngine.from_args(
    retriever=retriever,
    llm=OpenAI()
)

# Query:
response = query_engine.query("What is the forecast for ZEKO?")

print(response)
```

---

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: light)" srcset="https://cdn.auth0.com/website/sdks/logos/auth0_light_mode.png"   width="150">
    <source media="(prefers-color-scheme: dark)" srcset="https://cdn.auth0.com/website/sdks/logos/auth0_dark_mode.png" width="150">
    <img alt="Auth0 Logo" src="https://cdn.auth0.com/website/sdks/logos/auth0_light_mode.png" width="150">
  </picture>
</p>
<p align="center">Auth0 is an easy to implement, adaptable authentication and authorization platform. To learn more checkout <a href="https://auth0.com/why-auth0">Why Auth0?</a></p>
<p align="center">
This project is licensed under the Apache 2.0 license. See the <a href="/LICENSE"> LICENSE</a> file for more info.</p>
