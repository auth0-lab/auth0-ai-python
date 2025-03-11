import os
from typing import Any, Awaitable, Callable, TypedDict, Optional, Union
from openfga_sdk import OpenFgaClient, ConsistencyPreference, ClientConfiguration
from openfga_sdk.client import ClientCheckRequest
from openfga_sdk.credentials import Credentials, CredentialConfiguration
from auth0_ai.authorizers.types import AuthParams, ToolWithAuthHandler, ToolInput, ToolConfig, ToolOutput

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
    build_query: Callable[[Any], Awaitable[ClientCheckRequest]]

FGAInstance = Callable[
    [FGAAuthorizerOptions],
    Callable[
        [ToolWithAuthHandler[ToolInput, ToolOutput, ToolConfig], Optional[Callable[[Exception], Awaitable[ToolOutput]]]],
        Callable[[ToolInput, Optional[ToolConfig]], Awaitable[ToolOutput]]
    ]
]

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

    async def _authorize(self, options: FGAAuthorizerOptions, tool_context: Optional[Union[ToolInput, ToolConfig]] = None) -> Optional[bool]:
        query = await options["build_query"](tool_context)
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
                handler: ToolWithAuthHandler[ToolInput, ToolConfig, ToolOutput],
                on_error: Optional[Callable[[Exception], Awaitable[ToolOutput]]] = None
            ) -> Callable[[ToolInput, Optional[ToolConfig]], Awaitable[ToolOutput]]:
                
                async def wrapper(config: Optional[ToolConfig] = None, **input: ToolInput) -> ToolOutput:
                    try:
                        check_response = await authorizer._authorize(options, {**input, **(config or {})})
                        return await handler(AuthParams(allowed=check_response), input, *(config,) if config else ())
                    except Exception as e:
                        if callable(on_error):
                            return await on_error(e)
                        raise Exception("The user is not allowed to perform the action.") from e

                return wrapper
            
            return fga

        return instance
