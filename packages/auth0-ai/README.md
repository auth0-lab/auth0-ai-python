# Auth0 AI

This package provides base methods to use Auth0 with your AI use cases.

## Installation

```bash
pip install git+https://github.com/mustafadeel/auth0-ai-python.git@mod_struct#subdirectory=packages/auth0-ai
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

Create a .env file with the following deatils:

```
AUTH0_DOMAIN='<>'
AUTH0_CLIENT_ID='<>'
AUTH0_CLIENT_SECRET='<>'
AUTH0_REDIRECT_URI='<>'
AUTH0_SECRET_KEY='ALongRandomlyGeneratedString'
```

Create a python script for an interactive login, link and tool token example:

```python
from dotenv import find_dotenv, load_dotenv

import asyncio

from auth0_ai import AIAuth, User

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

auth_client = AIAuth()

async def login():
    return await auth_client.interactive_login(connection="Username-Password-Authentication", scope="openid email offline_access")

async def link(user_id, connection):
    linked = await auth_client.link(primary_user_id=user_id, connection=connection, scope="openid email")
    return linked

user1 = asyncio.run(login())

print("-" * 20)
print("USER DETAILS:", auth_client.get_session(user1))

link_status = asyncio.run(user1.link(connection="github"))

github_token = user1.get_3rd_party_token("github")
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
