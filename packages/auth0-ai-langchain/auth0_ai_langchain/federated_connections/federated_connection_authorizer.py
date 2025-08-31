import copy
from abc import ABC
from auth0_ai.authorizers.federated_connection_authorizer import FederatedConnectionAuthorizerBase, \
    FederatedConnectionAuthorizerParams
from auth0_ai.authorizers.types import Auth0ClientParams
from auth0_ai.interrupts.federated_connection_interrupt import FederatedConnectionInterrupt
from auth0_ai_langchain.utils.interrupt import to_graph_interrupt
from auth0_ai_langchain.utils.tool_wrapper import tool_wrapper
from langchain_core.tools import BaseTool
from langchain_core.runnables import ensure_config


async def default_get_refresh_token(*_, **__) -> str | None:
    return ensure_config().get("configurable", {}).get("_credentials", {}).get("refresh_token")

async def default_get_subject_access_token(*_, **__) -> str | None:
    """
    Returns the Auth0 *user* access token (from the LC graph config) to be used
    as the subject token in Token Vault exchange.
    """
    return ensure_config().get("configurable", {}).get("_credentials", {}).get("access_token")


class FederatedConnectionAuthorizer(FederatedConnectionAuthorizerBase, ABC):
    def __init__(
        self,
        params: FederatedConnectionAuthorizerParams,
        auth0: Auth0ClientParams = None,
    ):
        missing_refresh = params.refresh_token.value is None
        missing_subject_at = getattr(params, "subject_access_token",
                                     None) is None or params.subject_access_token.value is None

        if missing_refresh and missing_subject_at:
            params = copy.copy(params)
            params.subject_access_token.value = default_get_subject_access_token
        elif not missing_refresh and callable(default_get_refresh_token):
            if params.refresh_token.value is None:
                params = copy.copy(params)
                params.refresh_token.value = default_get_refresh_token

        super().__init__(params, auth0)

    def _handle_authorization_interrupts(self, err: FederatedConnectionInterrupt) -> None:
        raise to_graph_interrupt(err)

    def authorizer(self):
        def wrap_tool(tool: BaseTool) -> BaseTool:
            return tool_wrapper(tool, self.protect)

        return wrap_tool
