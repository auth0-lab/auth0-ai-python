import inspect
from abc import ABC
from auth0_ai.authorizers.ciba import CIBAAuthorizerBase
from llama_index.core.tools import FunctionTool

class CIBAAuthorizer(CIBAAuthorizerBase, ABC):
    def authorizer(self):
        def wrapped_tool(t: FunctionTool) -> FunctionTool:
            tool_fn = self.protect(
                lambda *_args, **_kwargs: { # TODO: review this
                    "thread_id": "",
                    "tool_name": t.metadata.name,
                    "tool_call_id": "",
                },
                t.acall if inspect.iscoroutinefunction(t.fn) else t.call
            )

            return FunctionTool(
                fn=tool_fn,
                async_fn=tool_fn,
                metadata=t.metadata,
                callback=t._callback,
                async_callback=t._async_callback,
            )
        
        return wrapped_tool
