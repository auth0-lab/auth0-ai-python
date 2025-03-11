from typing import TypedDict, Optional, Any, Callable, Awaitable, TypeVar

class AuthParams(TypedDict):
  allowed: Optional[bool]
  access_token: Optional[str]
  claims: Optional[Any]

ToolInput = TypeVar("ToolInput")
ToolConfig = TypeVar("ToolConfig")
ToolOutput = TypeVar("ToolOutput")

ToolWithAuthHandler = Callable[[AuthParams, ToolInput, Optional[ToolConfig]], Awaitable[ToolOutput]]
