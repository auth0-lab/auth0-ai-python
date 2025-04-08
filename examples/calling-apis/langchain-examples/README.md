# Calling APIs On User's Behalf with LangChain

## Getting Started

### Prerequisites

- An OpenAI account and API key create one [here](https://platform.openai.com).
  - [Use this page for instructions on how to find your OpenAI API key](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key).
- [LangGraph CLI](https://langchain-ai.github.io/langgraph/cloud/reference/cli/)
- A [Google OAuth 2.0 Client](https://console.cloud.google.com/apis/credentials) configured with access to the `https://www.googleapis.com/auth/calendar.freebusy` scope (Google Calendar API).
- An [Auth0](https://manage.auth0.com/) account with the following configuration:
  - **Google connection** set up with:
    - The client ID and secret from the previously created Google client.
    - The following settings:
      - **Offline access** enabled.
      - **https://www.googleapis.com/auth/calendar.freebusy** scope granted.
      - **Token Vault** enabled.
  - **Regular Web Application** set up with:
    - **Allowed Callback URLs**: `http://localhost:3000/login/callback`
    - **Allowed Logout URLs**: `http://localhost:3000/`
    - **Connections**: The previously created **Google connection**.
    - **Advanced Settings -> Grant Types**: **Token Exchange (Federated Connection)** and **Refresh Token**.

### Setup

Create a `.env` file using the format below:

```sh
# Auth0
AUTH0_DOMAIN="<auth0-domain>"
AUTH0_CLIENT_ID="<auth0-client-id>"
AUTH0_CLIENT_SECRET="<auth0-client-secret>"

# OpenAI
OPENAI_API_KEY="<openai-api-key>"
```

### How to run it

1.  **Install Dependencies**

    Use [Poetry](https://python-poetry.org/) to install the required dependencies:

    ```sh
    poetry install
    ```

2.  **Run LangGraph (dev mode)**

    ```sh
    poetry run langgraph_up
    ```

3.  **Run chat client**

    ```sh
    poetry run start
    ```

    > And navigate to `http://localhost:3000/`

4.  **Login with your Google account and ask the assistant about your availability**

    ```sh
    Am I available on September 25th at 9:15 AM?
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
