from dotenv import load_dotenv
from auth0_ai_llamaindex.auth0_ai import Auth0AI
from flask import request
from .auth import auth0

load_dotenv()

auth0_ai = Auth0AI()


async def refresh_token():
    store_options = {"request": request}
    auth_session = await auth0.get_session(store_options=store_options)
    return auth_session.get("refresh_token")

with_calendar_free_busy_access = auth0_ai.with_federated_connection(
    connection="google-oauth2",
    scopes=["https://www.googleapis.com/auth/calendar.freebusy"],
    refresh_token=refresh_token,
)
with_slack_access = auth0_ai.with_federated_connection(
    connection="sign-in-with-slack",
    scopes=["channels:read"],
    refresh_token=refresh_token,
)

with_github_access = auth0_ai.with_federated_connection(
    connection="github",
    scopes=["repo"],
    refresh_token=refresh_token,
)
