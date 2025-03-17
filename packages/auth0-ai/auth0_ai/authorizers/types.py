from typing import TypedDict, Optional, Any

class AuthParams(TypedDict):
  access_token: Optional[str]
  claims: Optional[Any]
