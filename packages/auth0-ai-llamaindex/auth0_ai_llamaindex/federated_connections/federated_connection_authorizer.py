from __future__ import annotations

from abc import ABC

from auth0_ai.authorizers.federated_connection_authorizer import (
    FederatedConnectionAuthorizerBase,
    FederatedConnectionAuthorizerParams,
)
from auth0_ai.authorizers.types import Auth0ClientParams
from auth0_ai_llamaindex.utils.tool_wrapper import tool_wrapper
from llama_index.core.tools import FunctionTool


class FederatedConnectionAuthorizer(FederatedConnectionAuthorizerBase, ABC):
    def __init__(
        self,
        params: FederatedConnectionAuthorizerParams,
        auth0: Auth0ClientParams = None,
    ):
        super().__init__(params, auth0)

    def authorizer(self):
        def wrap_tool(tool: FunctionTool) -> FunctionTool:
            return tool_wrapper(tool, self.protect)

        return wrap_tool
