from abc import ABC
from auth0_ai.authorizers.async_authorization import AsyncAuthorizerBase
from auth0_ai_llamaindex.utils.tool_wrapper import tool_wrapper
from llama_index.core.tools import FunctionTool

class AsyncAuthorizer(AsyncAuthorizerBase, ABC):
    def authorizer(self):
        def wrap_tool(tool: FunctionTool) -> FunctionTool:
            return tool_wrapper(tool, self.protect)
        
        return wrap_tool
