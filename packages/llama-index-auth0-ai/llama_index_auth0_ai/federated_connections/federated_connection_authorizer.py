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
            wrapped_fn = self.protect(
                lambda *_args, **_kwargs: { # TODO
                    # "tread_id": ensure_config().get("configurable", {}).get("tread_id"),
                    # "checkpoint_ns": ensure_config().get("configurable", {}).get("checkpoint_ns"),
                    # "run_id": ensure_config().get("configurable", {}).get("run_id"),
                    # "tool_call_id": ensure_config().get("configurable", {}).get("tool_call_id"),
                },
                t.call,
            )

            return FunctionTool(
                fn=wrapped_fn,
                async_fn=wrapped_fn,
                metadata=t.metadata,
                callback=t._callback,
                async_callback=t._async_callback,
            )
        
        return wrapped_tool
