from typing import Generic, Optional, TypeVar, Literal
from langchain_core.runnables.config import RunnableConfig
from auth0_ai.types import AuthorizerParams
from .ciba.ciba_graph.ciba_graph import CIBAGraph
from .ciba.ciba_graph.types import CIBAGraphOptions

N = TypeVar("N", bound=str)

def get_access_token(config: RunnableConfig) -> dict[Literal["type", "value"], str]:
    return config.get("configurable", {}).get("_credentials", {}).get("access_token")

class Auth0AI(Generic[N]):
    def __init__(self, config: Optional[AuthorizerParams] = None):
        self._graph: Optional[CIBAGraph[N]] = None
        self.config = config

    def with_CIBA(self, options: Optional[CIBAGraphOptions[N]] = None) -> CIBAGraph[N]:
        self._graph = CIBAGraph(options, self.config)
        return self._graph
