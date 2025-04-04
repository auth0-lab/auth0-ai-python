import inspect
import os
import time
from enum import Enum
from typing import Any, Awaitable, Callable, Optional, TypedDict, Union
from auth0 import Auth0Error
from auth0_ai.errors import AccessDeniedError, AuthorizationRequestExpiredError, UserDoesNotHavePushNotificationsError
from auth0_ai.token_response import TokenResponse
from auth0_ai.credentials import Credentials
from auth0_ai.authorizers.types import AuthorizerParams
from auth0.authentication.back_channel_login import BackChannelLogin
from auth0.authentication.get_token import GetToken

class CibaAuthorizerCheckResponse(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class AuthorizeResponse(TypedDict):
    auth_req_id: str
    expires_in: int
    interval: int

class CibaCheckReponse(TypedDict):
    token: Optional[TokenResponse]
    status: CibaAuthorizerCheckResponse

class CibaAuthorizerOptions(TypedDict):
    """
    Authorize Options to start CIBA flow.

    Attributes:
        scope (str): Space-separated list of OIDC and custom API scopes.
        binding_message (Union[str, Callable[..., Awaitable[str]]]): A human-readable string to display to the user, or a function that resolves it.
        user_id (Union[str, Callable[..., Awaitable[str]]]): The user id string, or a function that resolves it.
        audience (Optional[str]): Unique identifier of the audience for an issued token.
        request_expiry (Optional[int]): To configure a custom expiry time in seconds for CIBA request, pass a number between 1 and 300.
    """
    scope: str
    binding_message: Union[str, Callable[..., Awaitable[str]]]
    user_id: Union[str, Callable[..., Awaitable[str]]]
    audience: Optional[str]
    request_expiry: Optional[int]

class CIBAAuthorizer:
    def __init__(self, options: AuthorizerParams = None):
        params = {
            "domain": (options or {}).get("domain", os.getenv("AUTH0_DOMAIN")),
            "client_id": (options or {}).get("client_id", os.getenv("AUTH0_CLIENT_ID")),
            "client_secret": (options or {}).get("client_secret", os.getenv("AUTH0_CLIENT_SECRET")),
            "client_assertion_signing_key": (options or {}).get("client_assertion_signing_key"),
            "client_assertion_signing_alg": (options or {}).get("client_assertion_signing_alg"),
            "telemetry": (options or {}).get("telemetry"),
            "timeout": (options or {}).get("timeout"),
            "protocol": (options or {}).get("protocol")
        }

        # Remove keys with None values
        params = {k: v for k, v in params.items() if v is not None}

        self.back_channel_login = BackChannelLogin(**params)
        self.get_token = GetToken(**params)

    def _ensure_openid_scope(self, scope: str) -> str:
        scopes = scope.strip().split()
        if "openid" not in scopes:
            scopes.insert(0, "openid")
        return " ".join(scopes)

    async def _start(self, params: CibaAuthorizerOptions, tool_context: Optional[Any]) -> AuthorizeResponse:
        authorize_params = {
            "scope": self._ensure_openid_scope(params.get("scope")),
            "audience": params.get("audience"),
            "request_expiry": params.get("request_expiry"),
        }

        if isinstance(params.get("user_id"), str):
            user_id = params.get("user_id")
        elif inspect.iscoroutinefunction(params.get("user_id")):
            user_id = await params.get("user_id")(tool_context)
        else:
            user_id = params.get("user_id")(tool_context)

        authorize_params["login_hint"] = f'{{ "format": "iss_sub", "iss": "https://{self.back_channel_login.domain}/", "sub": "{user_id}" }}'

        if isinstance(params.get("binding_message"), str):
            authorize_params["binding_message"] = params.get("binding_message")
        elif inspect.iscoroutinefunction(params.get("binding_message")):
            authorize_params["binding_message"] = await params.get("binding_message")(tool_context)
        else:
            authorize_params["binding_message"] = params.get("binding_message")(tool_context)
        
        response = self.back_channel_login.back_channel_login(**authorize_params)
        return AuthorizeResponse(
            auth_req_id=response["auth_req_id"],
            expires_in=response["expires_in"],
            interval=response["interval"],
        )

    async def _check(self, auth_req_id: str) -> CibaCheckReponse:
        response = CibaCheckReponse(status=CibaAuthorizerCheckResponse.PENDING)

        try:
            result = self.get_token.backchannel_login(auth_req_id=auth_req_id)
            response["status"] = CibaAuthorizerCheckResponse.APPROVED
            response["token"] = {
                "access_token": result["access_token"],
                "id_token": result["id_token"],
                "expires_in": result["expires_in"],
                "scope": result["scope"],
                "refresh_token": result.get("refresh_token"),
                "token_type": result.get("token_type"),
            }
        except Auth0Error as e:
            if e.error_code == "invalid_request":
                response["status"] = CibaAuthorizerCheckResponse.EXPIRED
            elif e.error_code == "access_denied":
                response["status"] = CibaAuthorizerCheckResponse.REJECTED
            elif e.error_code == "authorization_pending":
                response["status"] = CibaAuthorizerCheckResponse.PENDING
        
        return response
    
    async def poll(self, params: AuthorizeResponse) -> Credentials:
        start_time = time.time()

        while time.time() - start_time < params.get("expires_in"):
            try:
                response = self.get_token.backchannel_login(auth_req_id=params.get("auth_req_id"))
                return Credentials(
                    access_token={
                        "type": response.get("token_type", "bearer"),
                        "value": response["access_token"],
                    }
                )
            except Auth0Error as e:
                if e.error_code == "invalid_request":
                    raise UserDoesNotHavePushNotificationsError(e.message)
                elif e.error_code == "access_denied":
                    raise AccessDeniedError(e.message)
                elif e.error_code == "authorization_pending":
                    time.sleep(params.get("interval"))
                else:
                    raise AuthorizationRequestExpiredError("Authorization request expired")

    @staticmethod
    async def start(options: CibaAuthorizerOptions, params: AuthorizerParams = None, tool_context: Any = None) -> AuthorizeResponse:
        authorizer = CIBAAuthorizer(params)
        return await authorizer._start(options, tool_context)

    @staticmethod
    async def check(auth_req_id: str, params: AuthorizerParams = None) -> CibaCheckReponse:
        authorizer = CIBAAuthorizer(params)
        return await authorizer._check(auth_req_id)
