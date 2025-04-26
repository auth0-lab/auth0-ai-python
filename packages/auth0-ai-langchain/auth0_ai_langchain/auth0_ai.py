from typing import Callable, Optional
from langchain_core.tools import BaseTool
from auth0_ai.authorizers.ciba import CIBAAuthorizerParams
from auth0_ai.authorizers.federated_connection_authorizer import FederatedConnectionAuthorizerParams
from auth0_ai.authorizers.types import Auth0ClientParams
from auth0_ai_langchain.ciba.ciba_authorizer import CIBAAuthorizer
from auth0_ai_langchain.federated_connections.federated_connection_authorizer import FederatedConnectionAuthorizer


class Auth0AI:
    """Provides decorators to secure LangChain tools using Auth0 authorization flows.
    """

    def __init__(self, auth0: Optional[Auth0ClientParams] = None):
        """Initializes the Auth0AI instance.

        Args:
            auth0 (Optional[Auth0ClientParams]): Parameters for the Auth0 client.
                If not provided, values will be automatically read from environment
                variables: `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, and `AUTH0_CLIENT_SECRET`.
        """
        self.auth0 = auth0

    def with_async_user_confirmation(self, **params: CIBAAuthorizerParams) -> Callable[[BaseTool], BaseTool]:
        """Protects a tool with the CIBA (Client-Initiated Backchannel Authentication) flow.

        Requires user confirmation via a second device (e.g., phone)
        before allowing the tool to execute.

        Args:
            **params: Parameters defined in `CIBAAuthorizerParams`.

        Returns:
            Callable[[BaseTool], BaseTool]: A decorator to wrap a LangChain tool.

        Example:
            ```python
            import os
            from auth0_ai_langchain.auth0_ai import Auth0AI
            from auth0_ai_langchain.ciba import get_ciba_credentials
            from langchain_core.runnables import ensure_config
            from langchain_core.tools import StructuredTool

            auth0_ai = Auth0AI()

            with_async_user_confirmation = auth0_ai.with_async_user_confirmation(
                scope="stock:trade",
                audience=os.getenv("AUDIENCE"),
                binding_message=lambda ticker, qty: f"Authorize the purchase of {qty} {ticker}",
                user_id=lambda *_, **__: ensure_config().get("configurable", {}).get("user_id")
            )

            def tool_function(ticker: str, qty: int) -> str:
                credentials = get_ciba_credentials()
                headers = {
                    "Authorization": f"{credentials['token_type']} {credentials['access_token']}",
                    # ...
                }
                # Call API

            trade_tool = with_async_user_confirmation(
                StructuredTool(
                    name="trade_tool",
                    description="Use this function to trade a stock",
                    func=tool_function,
                )
            )
            ```
        """
        authorizer = CIBAAuthorizer(CIBAAuthorizerParams(**params), self.auth0)
        return authorizer.authorizer()

    def with_federated_connection(self, **params: FederatedConnectionAuthorizerParams) -> Callable[[BaseTool], BaseTool]:
        """Enables a tool to obtain an access token from a federated identity provider (e.g., Google, Azure AD).

        The token can then be used within the tool to call third-party APIs on behalf of the user.

        Args:
            **params: Parameters defined in `FederatedConnectionAuthorizerParams`.

        Returns:
            Callable[[BaseTool], BaseTool]: A decorator to wrap a LangChain tool.

        Example:
            ```python
            from auth0_ai_langchain.auth0_ai import Auth0AI
            from auth0_ai_langchain.federated_connections import get_credentials_for_connection
            from langchain_core.tools import StructuredTool
            from datetime import datetime

            auth0_ai = Auth0AI()

            with_google_calendar_access = auth0_ai.with_federated_connection(
                connection="google-oauth2",
                scopes=["https://www.googleapis.com/auth/calendar.freebusy"]
            )

            def tool_function(date: datetime):
                credentials = get_credentials_for_connection()
                # Call Google API using credentials["access_token"]

            check_calendar_tool = with_google_calendar_access(
                StructuredTool(
                    name="check_user_calendar",
                    description="Use this function to check if the user is available on a certain date and time",
                    func=tool_function,
                )
            )
            ```
        """
        authorizer = FederatedConnectionAuthorizer(FederatedConnectionAuthorizerParams(**params), self.auth0)
        return authorizer.authorizer()
