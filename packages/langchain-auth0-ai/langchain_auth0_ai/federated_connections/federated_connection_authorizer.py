import uuid
from typing import Any
from abc import ABC
from auth0_ai.authorizers.federated_connection_authorizer import FederatedConnectionAuthorizerBase, FederatedConnectionAuthorizerParams
from auth0_ai.interrupts.federated_connection_interrupt import FederatedConnectionInterrupt
from auth0_ai.types import AuthorizerParams
from langchain_core.tools import StructuredTool, tool
from langchain_core.runnables.config import RunnableConfig
from ..utils.interrupt import to_graph_interrupt

def default_get_refresh_token():
    async def get_refresh_token(_: Any, config: RunnableConfig) -> str | None:
        return config.get("configurable", {}).get("_credentials", {}).get("refresh_token")
    return get_refresh_token

class FederatedConnectionAuthorizer(FederatedConnectionAuthorizerBase, ABC):
    def __init__(
        self, 
        auth0: AuthorizerParams, 
        config: FederatedConnectionAuthorizerParams
    ):
        middleware_instance_id = str(uuid.uuid4())
        refresh_token = config.get("refresh_token", default_get_refresh_token())
        
        super().__init__(auth0, {**config, "refresh_token": refresh_token})
        
        self.middleware_instance_id = middleware_instance_id
        self.protected_tools: list[str] = []
    
    def handle_authorization_interrupts(self, err: FederatedConnectionInterrupt) -> None:
        raise to_graph_interrupt(err)
    
    def authorizer(self):
        def wrapped_tool(t: StructuredTool) -> StructuredTool:
            return tool(
                self.protect(
                    lambda _params, ctx: {
                        "tread_id": getattr(ctx.configurable, "tread_id", None),
                        "checkpoint_ns": getattr(ctx.configurable, "checkpoint_ns", None),
                        "run_id": getattr(ctx.configurable, "run_id", None),
                        "tool_call_id": getattr(ctx.configurable, "tool_call_id", None),
                    },
                    t.invoke
                ),
                name=t.name,
                description=t.description,
                args_schema=t.args_schema,
            )
        
        return wrapped_tool
