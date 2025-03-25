# Calling APIs On User's Behalf with LangChain

## Getting Started

### Prerequisites

- An OpenAI account and API key create one [here](https://platform.openai.com).
  - [Use this page for instructions on how to find your OpenAI API key](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key).
- [LangGraph CLI](https://langchain-ai.github.io/langgraph/cloud/reference/cli/)
- An [Auth0](https://manage.auth0.com/) account with the following configuration:
  - **Regular Web Application** using the **Token Exchange (Federated Connection)** and **Refresh Token** grant types.
  - **Google client** configured with access to the `https://www.googleapis.com/auth/calendar.freebusy` scope (Google Calendar API).
  - **Google connection** set up with:
    - The client ID and secret from the previously created Google client.
    - The following settings:
      - **Offline access** enabled
      - **Calendar.Events.ReadOnly** scope granted
      - **Token storage and retrieval** enabled

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

4.  **Ask the assistant to TBD**

    ```sh
    TBD
    ```

### How this works

The graph is configured with two tools:

- **`check-country-holiday.py`**: Determines whether a specific date is a holiday in a given country.

  - **Example prompt:** _"Is April 25th a holiday in Bolivia?"_

- **`check-user-calendar.py`**: Checks if the logged-in user is available at a specified date and time.

  - **Example prompt:** _"Am I available on April 25th at 9:15 AM?"_

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
