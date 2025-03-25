import asyncio
import contextvars
import os
import requests
from typing import Awaitable, Callable, Generic, Optional, Any, TypedDict, Union
from .types import AuthorizerParams, AuthorizerToolParameter, ToolInput
from ..token_response import TokenResponse
from ..interrupts.auth0_interrupt import Auth0Interrupt
from ..interrupts.federated_connection_interrupt import FederatedConnectionError, FederatedConnectionInterrupt

class AsyncStorageValue(TypedDict):
    context: Any
    connection: str
    scopes: list[str]
    access_token: Optional[str]
    current_scopes: Optional[list[str]]

local_storage: contextvars.ContextVar[Optional[AsyncStorageValue]] = contextvars.ContextVar("local_storage", default=None)

def get_access_token_for_connection() -> str | None:
    store = local_storage.get()
    if store is None:
        raise RuntimeError("The tool must be wrapped with the with_federated_connections function.")
    return store["access_token"]

class FederatedConnectionAuthorizerParams(Generic[ToolInput]):
    def __init__(
        self,
        scopes: Union[
            AuthorizerToolParameter[ToolInput, list[str]],
            Callable[ToolInput, Union[list[str], Awaitable[list[str]]]],
            list[str],
        ],
        connection: Union[
            AuthorizerToolParameter[ToolInput, str],
            Callable[ToolInput, Union[str, Awaitable[str]]],
            str,
        ],
        refresh_token: Optional[Union[
            AuthorizerToolParameter[ToolInput, str | None],
            Callable[ToolInput, Union[str | None, Awaitable[str | None]]],
            str | None,
        ]] = None,
        access_token: Optional[Union[
            AuthorizerToolParameter[ToolInput, TokenResponse | None],
            Callable[ToolInput, Union[TokenResponse | None, Awaitable[TokenResponse | None]]],
            TokenResponse | None
        ]] = None,
    ):
        def wrap(val, result_type):
            if isinstance(val, AuthorizerToolParameter):
                return val
            return AuthorizerToolParameter[ToolInput, result_type](val)
       
        self.scopes = wrap(scopes, list[str])
        self.connection = wrap(connection, str)
        self.refresh_token = wrap(refresh_token, str | None)
        self.access_token = wrap(access_token, TokenResponse | None)

class FederatedConnectionAuthorizerBase(Generic[ToolInput]):
    def __init__(
        self,
        auth0: AuthorizerParams,
        params: FederatedConnectionAuthorizerParams[ToolInput]
    ):
        self.auth0 = auth0 or AuthorizerParams(
            domain=os.getenv("AUTH0_DOMAIN"),
            client_id=os.getenv("AUTH0_CLIENT_ID"),
            client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
        )
        self.params = params

        # Ensure either refreshToken or accessToken is provided
        if params.refresh_token.value is None and params.access_token.value is None:
            raise ValueError("Either refresh_token or access_token must be provided to initialize the Authorizer.")
        
        if params.refresh_token.value is not None and params.access_token.value is not None:
            raise ValueError("Only one of refresh_token or access_token can be provided to initialize the Authorizer.")
    
    def _handle_authorization_interrupts(self, err: Auth0Interrupt) -> None:
        raise err
    
    def validate_token(self, token_response: Optional[TokenResponse] = None):
        store = local_storage.get()
        if not store:
            raise RuntimeError("The tool must be wrapped with the FederationConnectionAuthorizer.")

        scopes = store["scopes"]
        connection = store["connection"]
        
        if token_response is None:
            raise FederatedConnectionInterrupt(
                f"Authorization required to access the Federated Connection API: {connection}",
                connection,
                scopes,
                scopes
            )

        current_scopes = token_response["scope"].split(" ") if token_response["scope"] else []
        missing_scopes = [s for s in scopes if s not in current_scopes]
        store["current_scopes"] = current_scopes
        
        if missing_scopes:
            raise FederatedConnectionInterrupt(
                f"Authorization required to access the Federated Connection API: {connection}. Missing scopes: {', '.join(missing_scopes)}",
                connection,
                scopes,
                current_scopes + scopes
            )

    async def get_access_token_impl(self, *args: ToolInput.args, **kwargs: ToolInput.kwargs) -> TokenResponse | None:
        store = local_storage.get()
        if not store:
            raise RuntimeError("The tool must be wrapped with the FederationConnectionAuthorizer.")
        
        connection = store["connection"]
        subject_token = await self.get_refresh_token(*args, **kwargs)
        if not subject_token:
            return None

        exchange_params = {
            "grant_type": "urn:auth0:params:oauth:grant-type:token-exchange:federated-connection-access-token",
            "client_id": self.auth0["client_id"],
            "client_secret": self.auth0["client_secret"],
            "subject_token_type": "urn:ietf:params:oauth:token-type:refresh_token",
            "subject_token": subject_token,
            "connection": connection,
            "requested_token_type": "http://auth0.com/oauth/token-type/federated-connection-access-token",
        }
        
        response = requests.post(f"https://{self.auth0['domain']}/oauth/token", json=exchange_params)
        
        if response.status_code != 200:
            return None
        
        return TokenResponse(**response.json())
    
    async def get_access_token(self, *args: ToolInput.args, **kwargs: ToolInput.kwargs) -> TokenResponse | None:
        if callable(self.params.refresh_token.value) or asyncio.iscoroutinefunction(self.params.refresh_token.value):
            token_response = await self.get_access_token_impl(*args, **kwargs)
        else:
            token_response = await self.params.access_token.resolve(*args, **kwargs)
        
        self.validate_token(token_response)
        return token_response
    
    async def get_refresh_token(self, *args: ToolInput.args, **kwargs: ToolInput.kwargs):
        return await self.params.refresh_token.resolve(*args, **kwargs)
    
    def protect(
        self,
        get_context: Callable[ToolInput, any],
        execute: Callable[ToolInput, any]
    ) -> Callable[ToolInput, any]:
        async def wrapped_execute(*args: ToolInput.args, **kwargs: ToolInput.kwargs):
            store = {
                "context": get_context(*args, **kwargs),
                "scopes": await self.params.scopes.resolve(*args, **kwargs),
                "connection": await self.params.connection.resolve(*args, **kwargs)
            }

            if local_storage.get():
                raise RuntimeError("Cannot nest tool calls that require federated connection authorization.")
            
            storage_token = local_storage.set(store)
            
            try:
                token_response = await self.get_access_token(*args, **kwargs)
                store["access_token"] = token_response["access_token"]
                return await execute(*args, **kwargs)
            except FederatedConnectionError as err:
                interrupt = FederatedConnectionInterrupt(
                    str(err),
                    store["connection"],
                    store["scopes"],
                    store["scopes"]
                )
                return self._handle_authorization_interrupts(interrupt)
            except Auth0Interrupt as err:
                return self._handle_authorization_interrupts(err)
            except Exception as err:
                raise err
            finally:
                local_storage.reset(storage_token)
        
        return wrapped_execute
