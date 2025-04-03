import copy
from abc import ABC
from auth0_ai.authorizers.federated_connection_authorizer import FederatedConnectionAuthorizerBase, FederatedConnectionAuthorizerParams
from auth0_ai.authorizers.types import AuthorizerParams
from auth0_ai.interrupts.federated_connection_interrupt import FederatedConnectionInterrupt
from langchain_core.tools import BaseTool, tool
from langchain_core.runnables import ensure_config
from ..utils.interrupt import to_graph_interrupt

async def get_refresh_token(*_args, **_kwargs) -> str | None:
    return ensure_config().get("configurable", {}).get("_credentials", {}).get("refresh_token")

class FederatedConnectionAuthorizer(FederatedConnectionAuthorizerBase, ABC):
    def __init__(
        self, 
        options: FederatedConnectionAuthorizerParams,
        config: AuthorizerParams = None,
    ):
        if options.refresh_token.value is None:
            options = copy.copy(options)
            options.refresh_token.value = get_refresh_token

        super().__init__(options, config)
    
    def _handle_authorization_interrupts(self, err: FederatedConnectionInterrupt) -> None:
        raise to_graph_interrupt(err)
    
    def authorizer(self):
        def wrapped_tool(t: BaseTool) -> BaseTool:
            async def execute_fn(*_args, **kwargs):
                return await t.ainvoke(input=kwargs)

            tool_fn = self.protect(
                lambda *_args, **_kwargs: {
                    "thread_id": ensure_config().get("configurable", {}).get("thread_id"),
                    "checkpoint_ns": ensure_config().get("configurable", {}).get("checkpoint_ns"),
                    "run_id": ensure_config().get("configurable", {}).get("run_id"),
                    "tool_call_id": ensure_config().get("configurable", {}).get("tool_call_id"), # TODO: review this
                },
                execute_fn
            )
            tool_fn.__name__ = t.name
            
            return tool(
                tool_fn,
                description=t.description,
                return_direct=t.return_direct,
                args_schema=t.args_schema,
                response_format=t.response_format,
            )
        
        return wrapped_tool
