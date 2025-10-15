import os
from dotenv import load_dotenv

from auth0_server_python.auth_server.server_client import ServerClient
from .stores import FlaskCookieTransactionStore, FlaskStatelessStateStore
load_dotenv()

# Instantiate the Auth0 Server Client
auth0 = ServerClient(
    domain=os.getenv("AUTH0_DOMAIN"),
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    authorization_params={"scope": "openid profile email offline_access"},
    redirect_uri=f"{os.getenv("APP_BASE_URL", "http://localhost:3000")}/auth/callback",
    transaction_store=FlaskCookieTransactionStore(
        secret=os.getenv("APP_SECRET_KEY", "SOME_RANDOM_SECRET_KEY")),
    state_store=FlaskStatelessStateStore(secret=os.getenv(
        "APP_SECRET_KEY", "SOME_RANDOM_SECRET_KEY")),
    secret=os.getenv("APP_SECRET_KEY", "SOME_RANDOM_SECRET_KEY")
)
