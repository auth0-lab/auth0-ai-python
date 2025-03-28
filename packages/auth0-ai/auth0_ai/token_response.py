from typing import TypedDict, Optional

class TokenResponse(TypedDict):
    access_token: str
    id_token: str
    expires_in: int
    scope: str
    refresh_token: Optional[str]
    token_type: Optional[str]
