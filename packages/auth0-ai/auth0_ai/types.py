from typing import Any, TypedDict, Optional, Union, Tuple

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

class AuthorizerParams(TypedDict):
    domain: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]
    client_assertion_signing_key: Optional[str]
    client_assertion_signing_alg: Optional[str]
    telemetry: Optional[bool]
    timeout: Optional[Union[float, Tuple[float, float]]]
    protocol: Optional[str]

class AuthParams(TypedDict):
  allowed: Optional[bool]
  access_token: Optional[str]
  claims: Optional[Any]