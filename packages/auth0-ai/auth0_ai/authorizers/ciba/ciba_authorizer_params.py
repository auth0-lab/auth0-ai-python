from typing import Awaitable, Callable, Generic, Optional, TypedDict, Union
from auth0_ai.authorizers.types import ToolInput

class CIBAAuthorizerParams(TypedDict, Generic[ToolInput]):
    """
    Authorize Options to start CIBA flow.

    Attributes:
        scope (list[str]): The scopes to request authorization for.
        binding_message (Union[str, Callable[..., Awaitable[str]]]): A human-readable string to display to the user, or a function that resolves it.
        user_id (Union[str, Callable[..., Awaitable[str]]]): The user id string, or a function that resolves it.
        audience (Optional[str]): The audience to request authorization for.
        request_expiry (Optional[int]): The time in seconds for the authorization request to expire, pass a number between 1 and 300 (default: 300 seconds = 5 minutes).
    """
    scopes: list[str]
    binding_message: Union[str, Callable[ToolInput, Awaitable[str]]]
    user_id: Union[str, Callable[ToolInput, Awaitable[str]]]
    audience: Optional[str]
    request_expiry: Optional[int]
