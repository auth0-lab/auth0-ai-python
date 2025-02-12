# Auth0 AI for LlamaIndex

This package integrates [LlamaIndex](https://docs.llamaindex.ai/en/stable/) with [Auth0 AI](https://www.auth0.ai/) for enhanced document retrieval capabilities.

## Installation

```bash
# pip install llama-index-auth0-ai
pip install git+https://github.com/auth0-lab/auth0-ai-python.git@main#subdirectory=packages/llama-index-auth0-ai
```

## Running Tests

1. **Install Dependencies**

   Use [Poetry](https://python-poetry.org/) to install the required dependencies:

   ```sh
   $ poetry install
   ```

2. **Run the tests**

   ```sh
   $ poetry run pytest tests
   ```

## Usage

```python
from llama_index.core import VectorStoreIndex, Document
from llama_index_auth0_ai import FGARetriever
from openfga_sdk.client.models import ClientCheckRequest
from openfga_sdk import ClientConfiguration
from openfga_sdk.credentials import CredentialConfiguration, Credentials

# Define some docs:
documents = [
    Document(text="This is a public doc", doc_id="public-doc"),
    Document(text="This is a private doc", doc_id="private-doc"),
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
        object=f'doc:{node.ref_doc_id}',
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
