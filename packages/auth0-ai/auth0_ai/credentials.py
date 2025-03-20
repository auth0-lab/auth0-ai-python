from typing import TypedDict, Optional

class Credential(TypedDict):
    type: str
    value: str

class Credentials(TypedDict):
    access_token: Credential
    id_token: Optional[Credential]
    refresh_token: Optional[Credential]
