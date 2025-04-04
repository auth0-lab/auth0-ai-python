from typing import Callable, Optional
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool
from auth0_ai.credentials import Credential
from auth0_ai.authorizers.types import AuthorizerParams
from auth0_ai.authorizers.federated_connection_authorizer import FederatedConnectionAuthorizerParams 
from .federated_connections.federated_connection_authorizer import FederatedConnectionAuthorizer
from .ciba.ciba_graph.ciba_graph import CIBAGraph
from .ciba.ciba_graph.types import CIBAGraphOptions

def get_access_token(config: RunnableConfig) -> Credential:
    """
    Fetch the access token obtained during the CIBA flow.

    Attributes:
        config(RunnableConfig): LangGraph runnable configuration instance.
    """
    return config.get("configurable", {}).get("_credentials", {}).get("access_token")

class Auth0AI():
    def __init__(self, config: Optional[AuthorizerParams] = None):
        self._graph: Optional[CIBAGraph] = None
        self.config = config

    def with_async_user_confirmation(self, **options: CIBAGraphOptions) -> CIBAGraph:
        """
        Initializes and registers a state graph for conditional trade operations using CIBA.

        Attributes:
            options (Optional[CIBAGraphOptions]): The base CIBA options.
        """
        self._graph = CIBAGraph(CIBAGraphOptions(**options), self.config)
        return self._graph
    
    def with_federated_connection(self, **options: FederatedConnectionAuthorizerParams) -> Callable[[BaseTool], BaseTool]:
        """
        Protects a tool execution with the Federated Connection authorizer.

        Attributes:
            options (FederatedConnectionAuthorizerParams): The Federated Connections authorizer options.
        """
        authorizer = FederatedConnectionAuthorizer(FederatedConnectionAuthorizerParams(**options), self.config)
        return authorizer.authorizer()
