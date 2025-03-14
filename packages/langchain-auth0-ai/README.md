# Auth0 AI for LangChain

`langchain-auth0-ai` is an SDK for building secure AI-powered applications using [Auth0](https://www.auth0.ai/), [Okta FGA](https://docs.fga.dev/) and [LangChain](https://python.langchain.com/docs/tutorials/).

## Installation

> [!WARNING]
> `langchain-auth0-ai` is currently under development and it is not intended to be used in production, and therefore has no official support.

```bash
pip install langchain-auth0-ai
```

## Async User Confirmation

Example [Async User Confirmation](../../examples/async-user-confirmation/langchain-examples/).

> TODO

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

## Authorization for Tools

Example [Authorization for Tools](../../examples/authorization-for-tools/langchain-examples/).

1. Create an instance of FGA Authorizer:

```python
from langchain_auth0_ai.fga.fga_authorizer import AuthParams, FGAAuthorizer, FGAAuthorizerOptions

fga = FGAAuthorizer.create()
```

**Note**: Here, you can configure and specify your FGA credentials. By `default`, they are read from environment variables:

```sh
FGA_STORE_ID="<fga-store-id>"
FGA_CLIENT_ID="<fga-client-id>"
FGA_CLIENT_SECRET="<fga-client-secret>"
```

2. Define the FGA query:

```python
from langchain_core.runnables import ensure_config

async def build_fga_query(params):
    user_id = ensure_config().get("configurable",{}).get("user_id")
    return {
        "user": f"user:{user_id}",
        "object": f"asset:{params.get("ticker")}",
        "relation": "can_buy",
        "context": {"current_time": datetime.now(timezone.utc).isoformat()}
    }

use_fga = fga(FGAAuthorizerOptions(
    build_query=build_fga_query
))
```

**Note**: The parameters given to the `build_query` function are the same as those provided to the tool function.

3. Wrap the tool:

```python
from langchain_core.tools import StructuredTool

async def buy_tool_function(auth: AuthParams, ticker: str, qty: int) -> str:
    allowed = auth.get("allowed", False)
    if allowed:
        # TODO: implement buy operation
        return f"Purchased {qty} shares of {ticker}"

    return f"The user is not allowed to buy {ticker}."

func=use_fga(buy_tool_function)

buy_tool = StructuredTool(
    func=func,
    coroutine=func,
    name="buy",
    description="Use this function to buy stocks",
)
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
