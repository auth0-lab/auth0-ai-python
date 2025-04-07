# LangChain Retrievers + Okta FGA

This example demonstrates how to combine [LangChain](https://python.langchain.com/docs/tutorials/) with robust authorization controls for RAG workflows. Using [Okta FGA](https://docs.fga.dev/), it ensures that users can only access documents they are authorized to view. The example retrieves relevant documents, enforces access permissions, and generates responses based only on authorized data, maintaining strict data security and preventing unauthorized access.

## Getting Started

### Prerequisites

- An Okta FGA account, you can create one [here](https://dashboard.fga.dev).
- An OpenAI account and API key, you can create one [here](https://platform.openai.com).
  - [Use this page for instructions on how to find your OpenAI API key](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key).

### Setup

Create a `.env` file using the format below:

```sh
# OpenAI
OPENAI_API_KEY="<openai-api-key>"

# Okta FGA
FGA_STORE_ID="<fga-store-id>"
FGA_CLIENT_ID="<fga-client-id>"
FGA_CLIENT_SECRET="<fga-client-secret>"
```

### How to run it

1.  **Install Dependencies**

    Use [Poetry](https://python-poetry.org/) to install the required dependencies:

    ```sh
    poetry install
    ```

2.  **Configure FGA store**

    ```sh
    poetry run fga_init
    ```

3.  **Run the Example**

    ```sh
    poetry run start
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
