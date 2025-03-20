from typing import Generic, TypedDict, Optional, Any, Union, Tuple, Callable, TypeVar, Awaitable, ParamSpec

class AuthParams(TypedDict):
  access_token: Optional[str]
  claims: Optional[Any]

class AuthorizerParams(TypedDict):
    """
    Base authorizer parameters.

    Attributes:
        domain (str): The domain of your Auth0 tenant.
        client_id (str): Your application's client ID.
        client_secret (str, optional): Your application's client secret.
        client_assertion_signing_key (str, optional): Private key used to sign the client assertion JWT.
        client_assertion_signing_alg (str, optional): Algorithm used to sign the client assertion JWT (defaults to 'RS256').
        telemetry (bool, optional): Enable or disable telemetry (defaults to True).
        timeout (float or tuple, optional): Change the requests connect and read timeout. Pass a tuple to specify both values separately or a float to set both to it (defaults to 5.0 for both).
        protocol (str, optional): Useful for testing (defaults to 'https').
    """
    domain: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]
    client_assertion_signing_key: Optional[str]
    client_assertion_signing_alg: Optional[str]
    telemetry: Optional[bool]
    timeout: Optional[Union[float, Tuple[float, float]]]
    protocol: Optional[str]

ToolInput = ParamSpec("ToolInput")
ToolResult = TypeVar("ToolResult")

class AuthorizerToolParameter(Generic[ToolInput, ToolResult]):
    def __init__(self, value: Union[
        ToolResult,
        Callable[ToolInput, Union[ToolResult, Awaitable[ToolResult]]]
    ]):
        self.value = value

def resolve_parameter(
    resolver: AuthorizerToolParameter,
    *context: ToolInput.args
) -> Union[ToolResult, Awaitable[ToolResult]]:
    if callable(resolver):
        return resolver(*context)
    return resolver
