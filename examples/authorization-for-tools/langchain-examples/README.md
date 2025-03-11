# Authorization for tools with LangChain

## Getting Started

### Prerequisites

- An Okta FGA account, you can create one [here](https://dashboard.fga.dev).
- An OpenAI account and API key, you can create one [here](https://platform.openai.com).
- [LangGraph CLI](https://langchain-ai.github.io/langgraph/cloud/reference/cli/)

### Setup

Create a `.env` file using the format below:

```sh
# OpenAI
OPENAI_API_KEY="<openai-api-key>"

# Okta FGA
FGA_STORE_ID="<fga-store-id>"
FGA_CLIENT_ID="<fga-client-id>"
FGA_CLIENT_SECRET="<fga-client-secret>"

# Langchain
LANGGRAPH_API_URL="http://localhost:54367"
```

### How to run it

1.  **Install Dependencies**

    Use [Poetry](https://python-poetry.org/) to install the required dependencies:

    ```sh
    $ poetry install
    ```

2.  **Configure FGA store**

    ```sh
    $ poetry run fga_init
    ```

3.  **Run Langraph**

    ```sh
    $ poetry run langgraph_up
    ```

4.  **Run chat client**

    ```sh
    $ poetry run start
    ```

5.  **Ask the assistant to purchase some shares**

    ```sh
    ? User · purchase 10 shares of ATKO
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
