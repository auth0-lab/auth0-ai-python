import os
import time
import jwt
from enum import Enum
from typing import Awaitable, Callable, Optional, TypedDict, Union
from langchain_auth0_ai.auth0_ai.errors import AccessDeniedError, AuthorizationRequestExpiredError, UserDoesNotHavePushNotificationsError
from langchain_auth0_ai.auth0_ai.types import AuthParams, AuthorizerParams, Credentials, TokenResponse
from auth0.authentication.back_channel_login import BackChannelLogin
from auth0.authentication.get_token import GetToken

class CibaAuthorizerCheckResponse(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class CibaResponse(TypedDict):
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
    def __init__(self, options: AuthorizerParams):
        params = {
            "domain": options.get("domain", os.getenv("AUTH0_DOMAIN")),
            "client_id": options.get("client_id", os.getenv("AUTH0_CLIENT_ID")),
            "client_secret": options.get("client_secret", os.getenv("AUTH0_CLIENT_SECRET")),
            "client_assertion_signing_key": options.get("client_assertion_signing_key"),
            "client_assertion_signing_alg": options.get("client_assertion_signing_alg"),
            "telemetry": options.get("telemetry"),
            "timeout": options.get("timeout"),
            "protocol": options.get("protocol")
        }

        self.back_channel_login = BackChannelLogin(**params)
        self.get_token = GetToken(**params)

    def _ensure_openid_scope(self, scope: str) -> str:
        scopes = scope.strip().split()
        if "openid" not in scopes:
            scopes.insert(0, "openid")
        return " ".join(scopes)

    async def _start[T](self, params: CibaAuthorizerOptions, tool_context: Optional[T]) -> Awaitable[CibaResponse]:
        authorize_params = {
            "scope": self._ensure_openid_scope(params.get("scope")),
            "audience": params.get("audience"),
            "request_expiry": params.get("request_expiry"),
            "subject_issuer_context": params.get("subject_issuer_context")  
        } 

        if isinstance(params.get("user_id"), str):
            authorize_params.user_id = f'{{ "format": "iss_sub", "iss": "https://{self.auth0.domain}/", "sub": "{params.get("user_id")}" }}'
        else:
            authorize_params.user_id = f'{{ "format": "iss_sub", "iss": "https://{self.auth0.domain}/", "sub": "{await params.get("user_id")(tool_context)}" }}'

        if isinstance(params.get("binding_message"), str):
            authorize_params.binding_message = params.get("binding_message")
        else:
            authorize_params.binding_message = await params.get("binding_message")(tool_context)
        
        response = await self.back_channel_login.backchannel_authorize(**authorize_params)

        return {
            "auth_req_id": response["auth_req_id"],
            "expires_in": response["expires_in"],
            "interval": response["interval"],
        }

    async def _check(self, auth_req_id: str) -> Awaitable[CibaCheckReponse]:
        response = {"token": None, "status": CibaAuthorizerCheckResponse.PENDING}

        try:
            result = self.get_token.backchannel_login(auth_req_id=auth_req_id)
            response["status"] = CibaAuthorizerCheckResponse.APPROVED
            response["token"] = {
                "accessToken": result["access_token"],
                "idToken": result["id_token"],
                "expiresIn": result["expires_in"],
                "scope": result["scope"],
                "refreshToken": result.get("refresh_token"),
                "tokenType": result.get("token_type"),
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

    async def _poll(self, params: CibaResponse) -> Awaitable[Credentials]:
        start_time = time.time()
        
        while time.time() - start_time < params.get("expires_in"):
            try:
                response = self.auth0.backchannel_grant(auth_req_id=params.get("auth_req_id"))
                return {
                    "accessToken": {
                        "type": response.get("token_type", "bearer"),
                        "value": response["access_token"],
                    }
                }
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
    async def authorize(options: CibaAuthorizerOptions, params: AuthorizerParams = None) -> Awaitable[AuthParams]:
        authorizer = CIBAAuthorizer(params)
        credentials = await authorizer._authorize(options)
        claims = jwt.decode(credentials["access_token"]["value"])
        return {"accessToken": credentials["access_token"]["value"], "claims": claims}

    @staticmethod
    async def start(options: CibaAuthorizerOptions, params: AuthorizerParams = None) -> Awaitable[CibaResponse]:
        authorizer = CIBAAuthorizer(params)
        return await authorizer._start(options)

    @staticmethod
    async def check(auth_req_id: str, params: AuthorizerParams = None) -> Awaitable[CibaCheckReponse]:
        authorizer = CIBAAuthorizer(params)
        return await authorizer._check(auth_req_id)