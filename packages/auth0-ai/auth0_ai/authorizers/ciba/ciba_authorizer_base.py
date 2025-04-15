from contextlib import asynccontextmanager
import contextvars
import inspect
import os
import time
from typing import Any, Callable, Generic, Optional, TypedDict, Union
from auth0 import Auth0Error
from auth0.authentication.back_channel_login import BackChannelLogin
from auth0.authentication.get_token import GetToken
from auth0_ai.credentials import TokenResponse
from auth0_ai.authorizers.ciba.ciba_authorizer_params import CIBAAuthorizerParams
from auth0_ai.authorizers.ciba.ciba_authorization_request import CIBAAuthorizationRequest
from auth0_ai.authorizers.types import Auth0ClientParams, ToolInput
from auth0_ai.interrupts.ciba_interrupts import AccessDeniedInterrupt, AuthorizationPendingInterrupt, AuthorizationPollingInterrupt, AuthorizationRequestExpiredInterrupt, InvalidGrantInterrupt, UserDoesNotHavePushNotificationsInterrupt

class AsyncStorageValue(TypedDict, total=False):
    context: Any
    credentials: Optional[TokenResponse]

_local_storage: contextvars.ContextVar[Optional[AsyncStorageValue]] = contextvars.ContextVar("local_storage", default=None)

def _get_local_storage() -> AsyncStorageValue:
    store = _local_storage.get()
    if store is None:
        raise RuntimeError("The tool must be wrapped with the with_async_user_confirmation function.")
    return store

def _update_local_storage(data: AsyncStorageValue) -> None:
    store = _get_local_storage()
    updated = store.copy()
    updated.update(data)
    _local_storage.set(updated)

@asynccontextmanager
async def _run_with_local_storage(data: AsyncStorageValue):
    if _local_storage.get() is not None:
        raise RuntimeError("Cannot nest tool calls that require CIBA authorization.")
    token = _local_storage.set(data)
    try:
        yield
    finally:
        _local_storage.reset(token)

def get_ciba_credentials() -> TokenResponse | None:
    store = _get_local_storage()
    return store.get("credentials")

class CIBAAuthorizerBase(Generic[ToolInput]):
    def __init__(self, params: CIBAAuthorizerParams[ToolInput], auth0: Auth0ClientParams = None):
        auth0 = {
            "domain": (auth0 or {}).get("domain", os.getenv("AUTH0_DOMAIN")),
            "client_id": (auth0 or {}).get("client_id", os.getenv("AUTH0_CLIENT_ID")),
            "client_secret": (auth0 or {}).get("client_secret", os.getenv("AUTH0_CLIENT_SECRET")),
            "client_assertion_signing_key": (auth0 or {}).get("client_assertion_signing_key"),
            "client_assertion_signing_alg": (auth0 or {}).get("client_assertion_signing_alg"),
            "telemetry": (auth0 or {}).get("telemetry"),
            "timeout": (auth0 or {}).get("timeout"),
            "protocol": (auth0 or {}).get("protocol")
        }

        # Remove keys with None values
        auth0 = {k: v for k, v in auth0.items() if v is not None}

        self.back_channel_login = BackChannelLogin(**auth0)
        self.get_token = GetToken(**auth0)
        self.params = params

    def _ensure_openid_scope(self, scope: str) -> str:
        scopes = scope.strip().split()
        if "openid" not in scopes:
            scopes.insert(0, "openid")
        return " ".join(scopes)
    
    def _handle_authorization_interrupts(self, err: Union[AuthorizationPendingInterrupt, AuthorizationPollingInterrupt]) -> None:
        raise err

    async def _start(self, *args: ToolInput.args, **kwargs: ToolInput.kwargs) -> CIBAAuthorizationRequest:
        authorize_params = {
            "scope": self._ensure_openid_scope(self.params.get("scope")),
            "audience": self.params.get("audience"),
            "request_expiry": self.params.get("request_expiry"),
        }

        if isinstance(self.params.get("user_id"), str):
            user_id = self.params.get("user_id")
        elif inspect.iscoroutinefunction(self.params.get("user_id")):
            user_id = await self.params.get("user_id")(*args, **kwargs)
        else:
            user_id = self.params.get("user_id")(*args, **kwargs)

        if not user_id:
            raise Exception("Unable to resolve user id")

        authorize_params["login_hint"] = f'{{ "format": "iss_sub", "iss": "https://{self.back_channel_login.domain}/", "sub": "{user_id}" }}'

        if isinstance(self.params.get("binding_message"), str):
            authorize_params["binding_message"] = self.params.get("binding_message")
        elif inspect.iscoroutinefunction(self.params.get("binding_message")):
            authorize_params["binding_message"] = await self.params.get("binding_message")(*args, **kwargs)
        else:
            authorize_params["binding_message"] = self.params.get("binding_message")(*args, **kwargs)
        
        try:
            requested_at = time.time()
            response = self.back_channel_login.back_channel_login(**authorize_params)
            return CIBAAuthorizationRequest(
                id=response["auth_req_id"],
                requested_at=requested_at,
                expires_in=response["expires_in"],
                interval=response["interval"],
            )
        except Auth0Error as e:
            if e.error_code == "invalid_request":
                raise UserDoesNotHavePushNotificationsInterrupt(e.message)

    def _poll(self, authorization_request: CIBAAuthorizationRequest) -> TokenResponse:
        start_time = time.time()

        while time.time() - start_time < authorization_request.get("expires_in"):
            try:
                response = self.get_token.backchannel_login(auth_req_id=authorization_request.get("id"))
                return TokenResponse(
                    access_token=response["access_token"],
                    id_token=response["id_token"],
                    expires_in=response["expires_in"],
                    scope=response["scope"],
                    refresh_token=response.get("refresh_token"),
                    token_type=response.get("token_type"),
                )
            except Auth0Error as e:
                if e.error_code == "invalid_request":
                    raise UserDoesNotHavePushNotificationsInterrupt(e.message)
                elif e.error_code == "access_denied":
                    raise AccessDeniedInterrupt(e.message, authorization_request)
                elif e.error_code == "invalid_grant":
                    raise InvalidGrantInterrupt(e.message, authorization_request)
                elif e.error_code == "authorization_pending" or e.error_code == "slow_down":
                    time.sleep(authorization_request.get("interval"))
        
        raise AuthorizationRequestExpiredInterrupt("The authorization request has expired.", authorization_request)
    
    def protect(
        self,
        get_context: Callable[ToolInput, any],
        execute: Callable[ToolInput, any]
    ) -> Callable[ToolInput, any]:
        async def wrapped_execute(*args: ToolInput.args, **kwargs: ToolInput.kwargs):
            store = {
                "context": get_context(*args, **kwargs),
            }

            async with _run_with_local_storage(store):
                try:
                    authorization_request = await self._start(*args, **kwargs)
                    credentials = self._poll(authorization_request)
                    _update_local_storage({"credentials": credentials})

                    if inspect.iscoroutinefunction(execute):
                        return await execute(*args, **kwargs)
                    else:
                        return execute(*args, **kwargs)
                except (AuthorizationPendingInterrupt, AuthorizationPollingInterrupt) as interrupt:
                    return self._handle_authorization_interrupts(interrupt)
        
        return wrapped_execute
