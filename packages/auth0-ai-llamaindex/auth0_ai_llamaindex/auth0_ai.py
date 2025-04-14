from typing import Callable, Optional
from llama_index.core.tools import BaseTool
from auth0_ai.authorizers.ciba import CIBAAuthorizerParams
from auth0_ai.authorizers.federated_connection_authorizer import FederatedConnectionAuthorizerParams
from auth0_ai.authorizers.types import Auth0ClientParams
from auth0_ai_llamaindex.ciba.ciba_authorizer import CIBAAuthorizer
from auth0_ai_llamaindex.federated_connections.federated_connection_authorizer import FederatedConnectionAuthorizer

class Auth0AI():
    def __init__(self, auth0: Optional[Auth0ClientParams] = None):
        self.auth0 = auth0

    def with_federated_connection(self, **params: FederatedConnectionAuthorizerParams) -> Callable[[BaseTool], BaseTool]:
        """
        Protects a tool execution with the Federated Connection authorizer.

        Attributes:
            params (FederatedConnectionAuthorizerParams): The Federated Connections authorizer params.
        """
        authorizer = FederatedConnectionAuthorizer(FederatedConnectionAuthorizerParams(**params), self.auth0)
        return authorizer.authorizer()

    def with_async_user_confirmation(self, **params: CIBAAuthorizerParams) -> Callable[[BaseTool], BaseTool]:
        """
        Protects a tool execution with the CIBA authorizer.

        Attributes:
            params (CIBAAuthorizerParams): The CIBA authorizer params.
        """
        authorizer = CIBAAuthorizer(CIBAAuthorizerParams(**params), self.auth0)
        return authorizer.authorizer()
