import os
import time
import jwt
from enum import Enum
from typing import Awaitable, Callable, Optional, TypedDict, Union
from auth0_ai.errors import AccessDeniedError, AuthorizationRequestExpiredError, UserDoesNotHavePushNotificationsError
from auth0_ai.types import AuthParams, AuthorizerParams, Credentials, TokenResponse
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
    scope: str
    binding_message: Union[str, Callable[..., Awaitable[str]]]
    user_id: Union[str, Callable[..., Awaitable[str]]]
    audience: Optional[str]
    request_expiry: Optional[str]
    subject_issuer_context: Optional[str]

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
        self.auth0_domain = params["domain"]
        self.client_id = params["client_id"]
        self.client_secret = params["client_secret"]

    def _ensure_openid_scope(self, scope: str) -> str:
        scopes = scope.strip().split()
        if "openid" not in scopes:
            scopes.insert(0, "openid")
        return " ".join(scopes)

    async def _start[T](self, params: CibaAuthorizerOptions, tool_context: Optional[T]) -> Awaitable[AuthorizeResponse]:
        authorize_params = {
            "scope": self._ensure_openid_scope(params.get("scope")),
            "audience": params.get("audience"),
            "request_expiry": params.get("request_expiry"),
            "subject_issuer_context": params.get("subject_issuer_context")
        }

        if isinstance(params.get("user_id"), str):
            authorize_params["login_hint"] = f'{{ "format": "iss_sub", "iss": "https://{self.auth0_domain}/", "sub": "{params.get("user_id")}" }}'
        else:
            authorize_params["login_hint"] = f'{{ "format": "iss_sub", "iss": "https://{self.auth0_domain}/", "sub": "{await params.get("user_id")(tool_context)}" }}'

        if isinstance(params.get("binding_message"), str):
            authorize_params["binding_message"] = params.get("binding_message")
        else:
            authorize_params["binding_message"] = await params.get("binding_message")(tool_context)

        # TODO: back_channel_login is not adding the content-type header, which is mandatory for '/bc-authorize'
        # response = self.back_channel_login.back_channel_login(**authorize_params)
        authorize_params["client_id"] = self.client_id
        authorize_params["client_secret"] = self.client_secret
        response = self.back_channel_login.authenticated_post(
            f"https://{self.auth0_domain}/bc-authorize",
            data={**authorize_params},
            headers={"Content-Type":"application/x-www-form-urlencoded"}
        )

        return AuthorizeResponse(
            auth_req_id=response["auth_req_id"],
            expires_in=response["expires_in"],
            interval=response["interval"],
        )

    async def _check(self, auth_req_id: str) -> Awaitable[CibaCheckReponse]:
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
        except Exception as e:
            error_code = getattr(e, "error", "")
            if error_code == "invalid_request":
                response["status"] = CibaAuthorizerCheckResponse.EXPIRED
            elif error_code == "access_denied":
                response["status"] = CibaAuthorizerCheckResponse.REJECTED
            elif error_code == "authorization_pending":
                response["status"] = CibaAuthorizerCheckResponse.PENDING
        
        return response

    async def _authorize[T](self, params: CibaAuthorizerOptions, tool_context: Optional[T]) -> Awaitable[Credentials]:
        return await self._poll(await self._start[T](**{**params, tool_context: tool_context}))

    async def _poll(self, params: AuthorizeResponse) -> Awaitable[Credentials]:
        start_time = time.time()
        
        while time.time() - start_time < params.get("expires_in"):
            try:
                response = self.auth0.backchannel_grant(auth_req_id=params.get("auth_req_id"))
                return Credentials(
                    access_token={
                        "type": response.get("token_type", "bearer"),
                        "value": response["access_token"],
                    }
                )
            except Exception as e:
                error_code = getattr(e, "error", "")
                error_description = getattr(e, "error_description", "")
                if error_code == "invalid_request":
                    raise UserDoesNotHavePushNotificationsError(error_description)
                elif error_code == "access_denied":
                    raise AccessDeniedError(error_description)
                elif error_code == "authorization_pending":
                    time.sleep(params.get("interval"))
                    continue
        
        raise AuthorizationRequestExpiredError("Authorization request expired")

    @staticmethod
    async def authorize[T](options: CibaAuthorizerOptions, params: AuthorizerParams = None, tool_context: T = None) -> Awaitable[AuthParams]:
        authorizer = CIBAAuthorizer(params)
        credentials = await authorizer._authorize(options, tool_context)
        claims = jwt.decode(credentials["access_token"]["value"])
        return AuthParams(access_token=credentials["access_token"]["value"], claims=claims)

    @staticmethod
    async def start[T](options: CibaAuthorizerOptions, params: AuthorizerParams = None, tool_context: T = None) -> Awaitable[AuthorizeResponse]:
        authorizer = CIBAAuthorizer(params)
        return await authorizer._start(options, tool_context)

    @staticmethod
    async def check(auth_req_id: str, params: AuthorizerParams = None) -> Awaitable[CibaCheckReponse]:
        authorizer = CIBAAuthorizer(params)
        return await authorizer._check(auth_req_id)