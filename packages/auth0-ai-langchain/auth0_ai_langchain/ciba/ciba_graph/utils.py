from typing import Optional, List
from .types import ProtectedTool, BaseState

def get_tool_definition(state: BaseState, tools: List[ProtectedTool]) -> Optional[dict]:
    message = state["messages"][-1]
    
    if not hasattr(message, "tool_calls") or not message.tool_calls:
        return None
    
    tool_calls = message.tool_calls
    tool = tool_calls[-1]
    metadata = next((t for t in tools if t.tool_name == tool["name"]), None)
    
    if not metadata:
        return None
    
    return {"metadata": metadata, "tool": tool, "message": message}