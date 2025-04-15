from typing import TypedDict, Optional

class TokenResponse(TypedDict):
    access_token: str
    id_token: str
    expires_in: int
    scope: str
    refresh_token: Optional[str]
    token_type: Optional[str]

class Credential(TypedDict):
    type: str
    value: str

class Credentials(TypedDict):
    access_token: Credential
    id_token: Optional[Credential]
    refresh_token: Optional[Credential]
