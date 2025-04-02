import inspect
from abc import ABC
from auth0_ai.authorizers.federated_connection_authorizer import FederatedConnectionAuthorizerBase, FederatedConnectionAuthorizerParams
from auth0_ai.authorizers.types import AuthorizerParams
from llama_index.core.tools import FunctionTool

class FederatedConnectionAuthorizer(FederatedConnectionAuthorizerBase, ABC):
    def __init__(
        self, 
        options: FederatedConnectionAuthorizerParams,
        config: AuthorizerParams = None,
    ):
        if options.refresh_token.value is None:
            raise ValueError('options.refresh_token must be provided.')

        super().__init__(options, config)
    
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
