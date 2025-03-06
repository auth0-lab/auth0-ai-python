from typing import Generic, Optional, TypeVar
from auth0_ai.types import AuthorizerParams
from .ciba.ciba_graph.ciba_graph import CIBAGraph
from .ciba.ciba_graph.types import CIBAGraphOptions

N = TypeVar("N", bound=str)

class Auth0AI(Generic[N]):
    def __init__(self, config: Optional[AuthorizerParams] = None):
        self._graph: Optional[CIBAGraph[N]] = None
        self.config = config

    def with_CIBA(self, options: Optional[CIBAGraphOptions[N]] = None) -> CIBAGraph[N]:
        self._graph = CIBAGraph(options, self.config)
        return self._graph
