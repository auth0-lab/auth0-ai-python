from typing import Concatenate, ParamSpec, TypedDict, Optional, Any, Callable, Awaitable, TypeVar, Union

class AuthParams(TypedDict):
  allowed: Optional[bool]
  access_token: Optional[str]
  claims: Optional[Any]

ToolInput = ParamSpec("ToolInput")
ToolOutput = TypeVar("ToolOutput")

ToolWithAuthHandler = Callable[Concatenate[AuthParams, ToolInput], Union[ToolOutput, Awaitable[ToolOutput]]]
