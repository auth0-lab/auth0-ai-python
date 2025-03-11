from typing import Optional
from langchain_core.runnables.config import RunnableConfig
from auth0_ai.types import AuthorizerParams, Credential
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

    def with_CIBA(self, options: Optional[CIBAGraphOptions] = None) -> CIBAGraph:
        """
        Initializes and registers a state graph for conditional trade operations using CIBA.

        Attributes:
            options (Optional[CIBAGraphOptions]): The base CIBA options.
        """
        self._graph = CIBAGraph(options, self.config)
        return self._graph
