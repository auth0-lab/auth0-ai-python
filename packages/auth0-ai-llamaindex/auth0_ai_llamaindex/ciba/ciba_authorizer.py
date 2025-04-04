# TODO: most part of this implementation should be moved to auth0-ai after updating auth0-ai-langchain
import contextvars
import inspect
from abc import ABC
from contextlib import asynccontextmanager
from typing import Any, Callable, Optional, TypedDict

from auth0_ai.authorizers.ciba_authorizer import CIBAAuthorizer as CIBAAuthorizerBase
from auth0_ai.authorizers.ciba_authorizer import CibaAuthorizerOptions
from auth0_ai.authorizers.types import AuthorizerParams, ToolInput
from auth0_ai.credentials import Credential
from llama_index.core.tools import FunctionTool


class AsyncStorageValue(TypedDict, total=False):
    context: Any
    access_token: Optional[Credential]


_local_storage: contextvars.ContextVar[Optional[AsyncStorageValue]] = contextvars.ContextVar(
    "local_storage", default=None)


def _get_local_storage() -> AsyncStorageValue:
    store = _local_storage.get()
    if store is None:
        raise RuntimeError(
            "The tool must be wrapped with the with_async_user_confirmation function.")
    return store


def _update_local_storage(data: AsyncStorageValue) -> None:
    store = _get_local_storage()
    updated = store.copy()
    updated.update(data)
    _local_storage.set(updated)


@asynccontextmanager
async def _run_with_local_storage(data: AsyncStorageValue):
    if _local_storage.get() is not None:
        raise RuntimeError(
            "Cannot nest tool calls that require async user confirmation.")
    token = _local_storage.set(data)
    try:
        yield
    finally:
        _local_storage.reset(token)


def get_access_token() -> str | None:
    store = _get_local_storage()
    return store.get("access_token")


class CIBAAuthorizer(CIBAAuthorizerBase, ABC):
    def __init__(
        self,
        options: CibaAuthorizerOptions,
        config: AuthorizerParams = None,
    ):
        super().__init__(config)
        self.options = options

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
                    authorize_response = await self._start(self.options, kwargs)
                    credentials = await self.poll(authorize_response)
                    _update_local_storage(
                        {"access_token": credentials["access_token"]})

                    if inspect.iscoroutinefunction(execute):
                        return await execute(*args, **kwargs)
                    else:
                        return execute(*args, **kwargs)
                except Exception as err:
                    raise err

        return wrapped_execute

    def authorizer(self):
        def wrapped_tool(t: FunctionTool) -> FunctionTool:
            tool_fn = self.protect(
                lambda *_args, **_kwargs: {  # TODO: review this
                    "thread_id": "",
                    "tool_name": t.metadata.name,
                    "tool_call_id": "",
                },
                t.acall if inspect.iscoroutinefunction(t.fn) else t.call
            )

            return FunctionTool(
                fn=tool_fn,
                async_fn=tool_fn,
                metadata=t.metadata,
                callback=t._callback,
                async_callback=t._async_callback,
            )

        return wrapped_tool
