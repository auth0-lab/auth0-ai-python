import inspect
import uuid
from typing import Callable
from llama_index.core.tools import FunctionTool
from auth0_ai_llamaindex.context import ai_context

def tool_wrapper(tool: FunctionTool, protect_fn: Callable) -> FunctionTool:
    async def tool_fn(*args, **kwargs):
        context = ai_context.get()
        if context is None:
            raise RuntimeError("AI context not set. Please use `set_ai_context(thread_id)` to initialize it.")

        thread_id = context["thread_id"]
        tool_call_id = str(uuid.uuid4())
        tool_name = tool.metadata.name

        return await protect_fn(
            lambda *_, **__: {
                "thread_id": thread_id,
                "tool_name": tool_name,
                "tool_call_id": tool_call_id,
            },
            tool.acall if inspect.iscoroutinefunction(tool.real_fn) else tool.call
        )(*args, **kwargs)

    return FunctionTool(
        fn=tool_fn,
        metadata=tool.metadata,
        callback=tool._callback,
        async_callback=tool._async_callback,
    )
