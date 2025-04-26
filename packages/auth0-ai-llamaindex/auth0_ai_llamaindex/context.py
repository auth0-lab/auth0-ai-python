import contextvars
from typing import Optional, TypedDict

class LlamaIndexContext(TypedDict):
    thread_id: str

ai_context: contextvars.ContextVar[Optional[LlamaIndexContext]] = contextvars.ContextVar("local_storage", default=None)

def set_ai_context(thread_id: str) -> None:
    """Set the context to associate with the retrieved credentials.

    Args:
        thread_id (str): The thread id to set in the context.
    """
    if not isinstance(thread_id, str) or not thread_id.strip():
        raise ValueError("thread_id must be a non-empty string")
    
    ai_context.set({"thread_id": thread_id})
