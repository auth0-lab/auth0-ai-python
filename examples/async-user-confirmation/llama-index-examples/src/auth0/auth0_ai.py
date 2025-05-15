import os
from dotenv import load_dotenv
from auth0_ai_llamaindex.auth0_ai import Auth0AI
from flask import request
from .auth import auth0

load_dotenv()

auth0_ai = Auth0AI()


async def user_id(**_kwargs):
    store_options = {"request": request}
    user = await auth0.get_user(store_options=store_options)
    return user.get("sub")

with_async_user_confirmation = auth0_ai.with_async_user_confirmation(
    scopes=["stock:trade"],
    audience=os.getenv("AUDIENCE"),
    binding_message=lambda ticker, qty: f"Authorize the purchase of {qty} {ticker}",
    user_id=user_id,
    # When this flag is set to `"block"`, the execution of the tool awaits until the user approves or rejects the request.
    # Given the asynchronous nature of the CIBA flow, this mode is only useful during development.
    on_authorization_request="block",
)
