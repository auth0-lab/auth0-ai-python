# Auth0 AI for LangChain

`auth0-ai-langchain` is an SDK for building secure AI-powered applications using [Auth0](https://www.auth0.ai/), [Okta FGA](https://docs.fga.dev/) and [LangChain](https://python.langchain.com/docs/tutorials/).

![Release](https://img.shields.io/pypi/v/auth0-ai-langchain) ![Downloads](https://img.shields.io/pypi/dw/auth0-ai-langchain) [![License](https://img.shields.io/:license-APACHE%202.0-blue.svg?style=flat)](https://opensource.org/license/apache-2-0)

## Installation

> [!WARNING]
> `auth0-ai-langchain` is currently under development and it is not intended to be used in production, and therefore has no official support.

```bash
pip install auth0-ai-langchain
```

## Authorization for Tools

The `FGAAuthorizer` can leverage Okta FGA to authorize tools executions. The `FGAAuthorizer.create` function can be used to create an authorizer that checks permissions before executing the tool.

Full example of [Authorization for Tools](https://github.com/auth0-lab/auth0-ai-python/tree/main/examples/authorization-for-tools/langchain-examples).

1. Create an instance of FGA Authorizer:

```python
from auth0_ai_langchain.fga.fga_authorizer import FGAAuthorizer, FGAAuthorizerOptions

fga = FGAAuthorizer.create()
```

**Note**: Here, you can configure and specify your FGA credentials. By `default`, they are read from environment variables:

```sh
FGA_STORE_ID="<fga-store-id>"
FGA_CLIENT_ID="<fga-client-id>"
FGA_CLIENT_SECRET="<fga-client-secret>"
```

2. Define the FGA query (`build_query`) and, optionally, the `on_unauthorized` handler:

```python
from langchain_core.runnables import ensure_config

async def build_fga_query(tool_input):
    user_id = ensure_config().get("configurable",{}).get("user_id")
    return {
        "user": f"user:{user_id}",
        "object": f"asset:{tool_input["ticker"]}",
        "relation": "can_buy",
        "context": {"current_time": datetime.now(timezone.utc).isoformat()}
    }

def on_unauthorized(tool_input):
    return f"The user is not allowed to buy {tool_input["qty"]} shares of {tool_input["ticker"]}."

use_fga = fga(FGAAuthorizerOptions(
    build_query=build_fga_query,
    on_unauthorized=on_unauthorized,
))
```

**Note**: The parameters given to the `build_query` and `on_unauthorized` functions are the same as those provided to the tool function.

3. Wrap the tool:

```python
from langchain_core.tools import StructuredTool

async def buy_tool_function(ticker: str, qty: int) -> str:
    # TODO: implement buy operation
    return f"Purchased {qty} shares of {ticker}"

func=use_fga(buy_tool_function)

buy_tool = StructuredTool(
    func=func,
    coroutine=func,
    name="buy",
    description="Use this function to buy stocks",
)
```

## Calling APIs On User's Behalf

The `Auth0AI.with_federated_connection` function exchanges user's refresh token taken from the runnable configuration (`config.configurable._credentials.refresh_token`) for a Federated Connection API token.

Full Example of [Calling APIs On User's Behalf](https://github.com/auth0-lab/auth0-ai-python/tree/main/examples/calling-apis/langchain-examples).

1. Define a tool with the proper authorizer:

```python
from auth0_ai_langchain.auth0_ai import Auth0AI
from auth0_ai_langchain.federated_connections import get_access_token_for_connection
from langchain_core.tools import StructuredTool

auth0_ai = Auth0AI()

with_google_calendar_access = auth0_ai.with_federated_connection(
    connection="google-oauth2",
    scopes=["https://www.googleapis.com/auth/calendar.freebusy"]
)

def tool_function(date: datetime):
    access_token = get_access_token_for_connection()
    # Call Google API

check_calendar_tool = with_google_calendar_access(
    StructuredTool(
        name="check_user_calendar",
        description="Use this function to check if the user is available on a certain date and time",
        func=tool_function,
        # ...
    )
)
```

2. Add a node to your graph for your tools:

```python
workflow = (
    StateGraph(State)
        .add_node(
            "tools",
            ToolNode(
                [
                    check_calendar_tool,
                    # ...
                ],
                # The error handler should be disabled to allow interruptions to be triggered from within tools.
                handle_tool_errors=False
            )
        )
        # ...
)
```

3. Handle interruptions properly. If the tool does not have access to user's Google Calendar, it will throw an interruption.

## RAG with FGA

The `FGARetriever` can be used to filter documents based on access control checks defined in Okta FGA. This retriever performs batch checks on retrieved documents, returning only the ones that pass the specified access criteria.

Full Example of [RAG Application](https://github.com/auth0-lab/auth0-ai-python/tree/main/examples/authorization-for-rag/langchain-examples).

Create a retriever instance using the `FGARetriever` class.

```python
from langchain.vectorstores import VectorStoreIndex
from langchain.schema import Document
from auth0_ai_langchain import FGARetriever
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
This project is licensed under the Apache 2.0 license. See the <a href="https://github.com/auth0-lab/auth0-ai-python/blob/main/LICENSE"> LICENSE</a> file for more info.</p>
