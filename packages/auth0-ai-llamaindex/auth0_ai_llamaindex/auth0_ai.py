from typing import Callable, Optional
from llama_index.core.tools import BaseTool
from auth0_ai.authorizers.types import AuthorizerParams
from auth0_ai.authorizers.federated_connection_authorizer import FederatedConnectionAuthorizerParams 
from auth0_ai.authorizers.ciba_authorizer import CibaAuthorizerOptions
from .federated_connections.federated_connection_authorizer import FederatedConnectionAuthorizer
from .ciba.ciba_authorizer import CIBAAuthorizer

class Auth0AI():
    def __init__(self, config: Optional[AuthorizerParams] = None):
        self.config = config

    def with_federated_connection(self, **options: FederatedConnectionAuthorizerParams) -> Callable[[BaseTool], BaseTool]:
        """
        Protects a tool execution with the Federated Connection authorizer.

        Attributes:
            options (FederatedConnectionAuthorizerParams): The Federated Connections authorizer options.
        """
        authorizer = FederatedConnectionAuthorizer(FederatedConnectionAuthorizerParams(**options), self.config)
        return authorizer.authorizer()

    def with_async_user_confirmation(self, **options: CibaAuthorizerOptions) -> Callable[[BaseTool], BaseTool]:
        """
        Protects a tool execution with the CIBA authorizer.

        Attributes:
            options (CibaAuthorizerOptions): The CIBA authorizer options.
        """
        authorizer = CIBAAuthorizer(CibaAuthorizerOptions(**options), self.config)
        return authorizer.authorizer()
