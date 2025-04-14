from abc import ABC
from typing import Union
from auth0_ai.authorizers.ciba import CIBAAuthorizerBase
from auth0_ai.interrupts import AuthorizationPendingInterrupt, AuthorizationPollingInterrupt
from auth0_ai_langchain.utils.interrupt import to_graph_interrupt
from langchain_core.tools import BaseTool, tool
from langchain_core.runnables import ensure_config

class CIBAAuthorizer(CIBAAuthorizerBase, ABC):
    def _handle_authorization_interrupts(self, err: Union[AuthorizationPendingInterrupt, AuthorizationPollingInterrupt]) -> None:
        raise to_graph_interrupt(err)
    
    def authorizer(self):
        def wrapped_tool(t: BaseTool) -> BaseTool:
            async def execute_fn(*_args, **kwargs):
                return await t.ainvoke(input=kwargs)

            tool_fn = self.protect(
                lambda *_, **__: {
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
