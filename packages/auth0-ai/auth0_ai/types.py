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
    """
    Base authorization parameters.

    Attributes:
        domain (str): The domain of your Auth0 tenant.
        client_id (str): Your application's client ID.
        client_secret (str, optional): Your application's client secret.
        client_assertion_signing_key (str, optional): Private key used to sign the client assertion JWT.
        client_assertion_signing_alg (str, optional): Algorithm used to sign the client assertion JWT (defaults to 'RS256').
        telemetry (bool, optional): Enable or disable telemetry (defaults to True).
        timeout (float or tuple, optional): Change the requests connect and read timeout. Pass a tuple to specify both values separately or a float to set both to it (defaults to 5.0 for both).
        protocol (str, optional): Useful for testing (defaults to 'https').
    """
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