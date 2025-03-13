import asyncio
import functools
import inspect
import os
from typing import Any, Awaitable, Callable, TypedDict, Optional, Union
from openfga_sdk import OpenFgaClient, ConsistencyPreference, ClientConfiguration
from openfga_sdk.client import ClientCheckRequest
from openfga_sdk.credentials import Credentials, CredentialConfiguration
from auth0_ai.authorizers.types import AuthParams, ToolInput, ToolOutput, ToolWithAuthHandler

class FGAAuthorizerCredentialsConfig(TypedDict, total=False):
    api_issuer: str
    api_audience: str
    client_id: str
    client_secret: str

class FGAAuthorizerCredentials(TypedDict, total=False):
    method: Any
    config: FGAAuthorizerCredentialsConfig

class FGAAuthorizerParams(TypedDict, total=False):
    api_url: str
    store_id: str
    authorization_model_id: Optional[str]
    credentials: FGAAuthorizerCredentials

class FGAAuthorizerOptions(TypedDict):
    build_query: Callable[[Any], Union[ClientCheckRequest, Awaitable[ClientCheckRequest]]]

FGAInstance = Callable[
    [FGAAuthorizerOptions],
    Callable[
        [ToolWithAuthHandler[ToolInput, ToolOutput], Optional[Callable[[Exception], Union[ToolOutput, Awaitable[ToolOutput]]]]],
        Callable[ToolInput, Awaitable[ToolOutput]]
    ]
]

def _merge_args_kwargs(sig: inspect.Signature, *args, **kwargs) -> dict:
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)

class FGAAuthorizer:
    def __init__(self, params: Optional[FGAAuthorizerParams] = None):
        params = params or {}
        credentials = params.get("credentials", {})
        credentials_config = credentials.get("config", {})
        
        self.fga_configuration = ClientConfiguration(
            api_url=params.get("api_url", os.getenv("FGA_API_URL", "https://api.us1.fga.dev")),
            store_id=params.get("store_id", os.getenv("FGA_STORE_ID")),
            authorization_model_id=params.get("authorization_model_id", os.getenv("FGA_MODEL_ID")),
            credentials=Credentials(
                method=credentials.get("method", "client_credentials"),
                configuration=CredentialConfiguration(
                    api_issuer=credentials_config.get("api_issuer", os.getenv("FGA_API_TOKEN_ISSUER", "auth.fga.dev")),
                    api_audience=credentials_config.get("api_audience", os.getenv("FGA_API_AUDIENCE", "https://api.us1.fga.dev/")),
                    client_id=credentials_config.get("client_id", os.getenv("FGA_CLIENT_ID")),
                    client_secret=credentials_config.get("client_secret", os.getenv("FGA_CLIENT_SECRET")),
                )
            )
        )

    async def _authorize(self, options: FGAAuthorizerOptions, tool_context: Optional[Any] = None) -> Optional[bool]:
        if asyncio.iscoroutinefunction(options["build_query"]):
            query = await options["build_query"](tool_context)
        else:
            query = options["build_query"](tool_context)

        async with OpenFgaClient(self.fga_configuration) as fga_client:
            response = await fga_client.check(ClientCheckRequest(**query), {"consistency": ConsistencyPreference.HIGHER_CONSISTENCY})
            await fga_client.close()
            return response.allowed

    @staticmethod
    async def authorize(options: FGAAuthorizerOptions, params: Optional[FGAAuthorizerParams] = None) -> AuthParams:
        authorizer = FGAAuthorizer(params)
        check_response = await authorizer._authorize(options)
        return AuthParams(allowed=check_response)

    @staticmethod
    def create(params: Optional[FGAAuthorizerParams] = None) -> FGAInstance:
        authorizer = FGAAuthorizer(params)

        def instance(options: FGAAuthorizerOptions):
            def fga(
                handler: ToolWithAuthHandler[ToolInput, ToolOutput],
                on_error: Optional[Callable[[Exception], Union[ToolOutput, Awaitable[ToolOutput]]]] = None
            ) -> Callable[ToolInput, Awaitable[ToolOutput]]:
                
                # Get the original handler's signature and remove the first parameter (authParams)
                original_sig = inspect.signature(handler)
                new_params = list(original_sig.parameters.values())[1:]
                new_sig = original_sig.replace(parameters=new_params)
                
                @functools.wraps(handler)
                async def wrapper(*args: ToolInput.args, **kwargs: ToolInput.kwargs) -> ToolOutput:
                    try:
                        merged_args = _merge_args_kwargs(new_sig, *args, **kwargs)
                        check_response = await authorizer._authorize(options, merged_args)

                        if asyncio.iscoroutinefunction(handler):
                            return await handler(AuthParams(allowed=check_response), *args, **kwargs)
                        else:
                            return handler(AuthParams(allowed=check_response), *args, **kwargs)
                    except Exception as e:
                        if callable(on_error):
                            if asyncio.iscoroutinefunction(on_error):
                                return await on_error(e)
                            else:
                                return on_error(e)
                        
                        raise Exception("The user is not allowed to perform the action.") from e

                # Set the modified signature on the wrapper
                wrapper.__signature__ = new_sig
                return wrapper
            
            return fga

        return instance
