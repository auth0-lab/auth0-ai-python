from typing import Awaitable, Callable, Generic, Literal, Optional, TypedDict, Union
from auth0_ai.authorizers.types import ToolInput
from auth0_ai.stores import Store

class CIBAAuthorizerParams(TypedDict, Generic[ToolInput]):
    """
    Authorize Options to start CIBA flow.

    Attributes:
        scope (list[str]): The scopes to request authorization for.
        binding_message (Union[str, Callable[..., Awaitable[str]]]): A human-readable string to display to the user, or a function that resolves it.
        user_id (Union[str, Callable[..., Awaitable[str]]]): The user id string, or a function that resolves it.
        store (Store, optional): An store used to temporarly store the authorization response data while the user is completing the authorization in another device (default: InMemoryStore).
        audience (str, optional): The audience to request authorization for.
        request_expiry (int, optional): The time in seconds for the authorization request to expire, pass a number between 1 and 300 (default: 300 seconds = 5 minutes).
        on_authorization_request (string, optional): The behavior when the authorization request is made. Expected values:
            - "interrupt" (default): The tool execution is interrupted until the user completes the authorization.
            - "block": The tool execution is blocked until the user completes the authorization. This mode is only useful for development purposes and should not be used in production.
    """
    scopes: list[str]
    binding_message: Union[str, Callable[ToolInput, Awaitable[str]]]
    user_id: Union[str, Callable[ToolInput, Awaitable[str]]]
    store: Optional[Store]
    audience: Optional[str]
    request_expiry: Optional[int]
    on_authorization_request: Optional[Literal["block", "interrupt"]]

