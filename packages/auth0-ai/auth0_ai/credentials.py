from typing import TypedDict, Optional

class AuthorizationDetails(TypedDict):
    type: str

class TokenResponse(TypedDict):
    access_token: str
    expires_in: int
    scope: list[str]
    token_type: Optional[str]
    id_token: Optional[str]
    refresh_token: Optional[str]
    authorization_details: Optional[list[AuthorizationDetails]]