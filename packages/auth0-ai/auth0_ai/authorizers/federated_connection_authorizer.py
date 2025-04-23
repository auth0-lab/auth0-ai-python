import asyncio
import contextvars
import hashlib
import inspect
import json
import os
from contextlib import asynccontextmanager
from typing import Awaitable, Callable, Generic, Optional, Any, TypedDict, Union
from auth0 import Auth0Error
from auth0.authentication.get_token import GetToken
from auth0_ai.authorizers.context import AuthContext, ContextGetter, ns_from_context
from auth0_ai.authorizers.types import Auth0ClientParams, AuthorizerToolParameter, ToolInput
from auth0_ai.credentials import TokenResponse
from auth0_ai.interrupts.auth0_interrupt import Auth0Interrupt
from auth0_ai.interrupts.federated_connection_interrupt import FederatedConnectionError, FederatedConnectionInterrupt
from auth0_ai.stores import Store, SubStore, InMemoryStore
from auth0_ai.utils import omit

class AsyncStorageValue(TypedDict):
    context: Any
    connection: str
    scopes: list[str]
    current_scopes: Optional[list[str]]
    credentials: Optional[TokenResponse]

_local_storage: contextvars.ContextVar[Optional[AsyncStorageValue]] = contextvars.ContextVar("local_storage", default=None)

def _get_local_storage() -> AsyncStorageValue:
    store = _local_storage.get()
    if store is None:
        raise RuntimeError("The tool must be wrapped with the with_federated_connection function.")
    return store

def _update_local_storage(data: AsyncStorageValue) -> None:
    store = _get_local_storage()
    updated = store.copy()
    updated.update(data)
    _local_storage.set(updated)

@asynccontextmanager
async def _run_with_local_storage(data: AsyncStorageValue):
    if _local_storage.get() is not None:
        raise RuntimeError("Cannot nest tool calls that require federated connection authorization.")
    token = _local_storage.set(data)
    try:
        yield
    finally:
        _local_storage.reset(token)

def get_credentials_for_connection() -> TokenResponse | None:
    store = _get_local_storage()
    return store.get("credentials")

class FederatedConnectionAuthorizerParams(Generic[ToolInput]):
    def __init__(
        self,
        scopes: list[str],
        connection: str,
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
        store: Optional[Store] = None,
        credentials_context: Optional[AuthContext] = "thread"
    ):
        """
        Parameters for the federated connection authorizer.

        Args:
            scopes: The scopes required in the access token of the federated connection provider.
            connection: The connection name of the federated connection provider.
            refresh_token: Optional. The Auth0 refresh token to exchange for an federated connection access token. Can be:
                - A string or None
                - A callable that receives the tool input and returns the user refresh token (sync or async)
            access_token: Optional. The federated connection access token if available in the tool context. Can be:
                - A `TokenResponse`
                - A callable that receives the tool input and returns a `TokenResponse` (sync or async)
            store: Optional. An store used to temporarly store the authorization response data while the user is completing the authorization in another device (default: InMemoryStore).
            credentials_context: Optional. Defines the scope of credential sharing. Can be:
                - "thread" (default): Credentials are shared across all tools using the same authorizer within the current thread.
                - "agent": Credentials are shared globally across all threads and tools in the agent.
                - "tool": Credentials are shared across multiple calls to the same tool within the same thread.
                - "tool-call": Credentials are valid only for a single invocation of the tool.
        """

        def wrap(val, result_type):
            if isinstance(val, AuthorizerToolParameter):
                return val
            return AuthorizerToolParameter[ToolInput, result_type](val)
       
        self.scopes = scopes
        self.connection = connection
        self.refresh_token = wrap(refresh_token, str | None)
        self.access_token = wrap(access_token, TokenResponse | None)
        self.store = store
        self.credentials_context = credentials_context

class FederatedConnectionAuthorizerBase(Generic[ToolInput]):
    def __init__(
        self,
        params: FederatedConnectionAuthorizerParams[ToolInput],
        config: Auth0ClientParams = None,
    ):
        self.params = params
        auth0 = {
            "domain": (config or {}).get("domain", os.getenv("AUTH0_DOMAIN")),
            "client_id": (config or {}).get("client_id", os.getenv("AUTH0_CLIENT_ID")),
            "client_secret": (config or {}).get("client_secret", os.getenv("AUTH0_CLIENT_SECRET")),
            "client_assertion_signing_key": (config or {}).get("client_assertion_signing_key"),
            "client_assertion_signing_alg": (config or {}).get("client_assertion_signing_alg"),
            "telemetry": (config or {}).get("telemetry"),
            "timeout": (config or {}).get("timeout"),
            "protocol": (config or {}).get("protocol")
        }

        # Remove keys with None values
        self.auth0 = {k: v for k, v in auth0.items() if v is not None}
        self.get_token = GetToken(**self.auth0)

        # TODO: consider moving this to Auth0AI classes
        sub_store = SubStore(params.store or InMemoryStore()).create_sub_store("AUTH0_AI_FEDERATED_CONNECTION")

        instance_id = self._get_instance_id()

        self.credentials_store = SubStore[TokenResponse](sub_store, {
            "base_namespace": [instance_id, "credentials"],
            "get_ttl": lambda credential: credential["expires_in"] * 1000 if "expires_in" in credential else None
        })

        # Ensure either refreshToken or accessToken is provided
        if params.refresh_token.value is None and params.access_token.value is None:
            raise ValueError("Either refresh_token or access_token must be provided to initialize the Authorizer.")
        
        if params.refresh_token.value is not None and params.access_token.value is not None:
            raise ValueError("Only one of refresh_token or access_token can be provided to initialize the Authorizer.")
    
    def _handle_authorization_interrupts(self, err: Auth0Interrupt) -> None:
        raise err
    
    def _get_instance_id(self) -> str:
        props = {
            "auth0": omit(self.auth0, ["client_secret", "client_assertion_signing_key"]),
            "params": omit(self.params, ["store", "refresh_token", "access_token"])
        }
        sh = json.dumps(props, sort_keys=True, separators=(",", ":"))
        return hashlib.md5(sh.encode("utf-8")).hexdigest()
    
    def validate_token(self, token_response: Optional[TokenResponse] = None):
        store = _get_local_storage()
        scopes = store["scopes"]
        connection = store["connection"]
        
        if token_response is None:
            raise FederatedConnectionInterrupt(
                f"Authorization required to access the Federated Connection API: {connection}",
                connection,
                scopes,
                scopes
            )

        current_scopes = token_response["scope"]
        missing_scopes = [s for s in scopes if s not in current_scopes]
        _update_local_storage({"current_scopes": current_scopes})
        
        if missing_scopes:
            raise FederatedConnectionInterrupt(
                f"Authorization required to access the Federated Connection API: {connection}. Missing scopes: {', '.join(missing_scopes)}",
                connection,
                scopes,
                current_scopes + scopes
            )

    async def get_access_token_impl(self, *args: ToolInput.args, **kwargs: ToolInput.kwargs) -> TokenResponse | None:
        store = _get_local_storage()
        
        connection = store["connection"]
        subject_token = await self.get_refresh_token(*args, **kwargs)
        if not subject_token:
            return None
        
        try:
            response = self.get_token.access_token_for_connection(
                subject_token_type="urn:ietf:params:oauth:token-type:refresh_token",
                subject_token=subject_token,
                requested_token_type="http://auth0.com/oauth/token-type/federated-connection-access-token",
                connection=connection,
            )
            
            return TokenResponse(
                access_token=response["access_token"],
                expires_in=response["expires_in"],
                scope=response.get("scope", "").split(),
                token_type=response.get("token_type"),
                id_token=response.get("id_token"),
                refresh_token=response.get("refresh_token"),
            )
        except Auth0Error as err:
            raise FederatedConnectionError(err.message) if 400 <= err.status_code <= 499 else err
    
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
        get_context: ContextGetter[ToolInput],
        execute: Callable[ToolInput, any]
    ) -> Callable[ToolInput, any]:
        async def wrapped_execute(*args: ToolInput.args, **kwargs: ToolInput.kwargs):
            context = get_context(*args, **kwargs)
            local_store = {
                "context": context,
                "scopes": self.params.scopes,
                "connection": self.params.connection
            }

            async with _run_with_local_storage(local_store):
                credentials_ns = ns_from_context(self.params.credentials_context, context)

                try:
                    credentials = await self.credentials_store.get(credentials_ns, "credential")
                    
                    if not credentials:
                        credentials = await self.get_access_token(*args, **kwargs)
                        await self.credentials_store.put(credentials_ns, "credential", credentials)
                    
                    _update_local_storage({"credentials": credentials})

                    if inspect.iscoroutinefunction(execute):
                        return await execute(*args, **kwargs)
                    else:
                        return execute(*args, **kwargs)
                except FederatedConnectionError as err:
                    self.credentials_store.delete(credentials_ns, "credential")
                    interrupt = FederatedConnectionInterrupt(
                        str(err),
                        local_store["connection"],
                        local_store["scopes"],
                        local_store["scopes"]
                    )
                    return self._handle_authorization_interrupts(interrupt)
                except Auth0Interrupt as err:
                    self.credentials_store.delete(credentials_ns, "credential")
                    return self._handle_authorization_interrupts(err)
        
        return wrapped_execute
