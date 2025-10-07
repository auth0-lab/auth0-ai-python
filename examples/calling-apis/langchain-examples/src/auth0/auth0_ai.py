from dotenv import load_dotenv
from auth0_ai_langchain.auth0_ai import Auth0AI

load_dotenv()

auth0_ai = Auth0AI()


with_calendar_free_busy_access = auth0_ai.with_token_vault(
    connection="google-oauth2",
    scopes=["https://www.googleapis.com/auth/calendar.freebusy"]
)

with_slack_access = auth0_ai.with_token_vault(
    connection="sign-in-with-slack",
    scopes=["channels:read"]
)

with_github_access = auth0_ai.with_token_vault(
    connection="github",
    scopes=["repo"],
)
