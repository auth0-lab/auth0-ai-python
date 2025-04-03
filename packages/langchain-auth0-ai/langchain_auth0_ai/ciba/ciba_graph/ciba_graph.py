from typing import Awaitable, Hashable, List, Optional, Callable, Any, Union
from langchain_core.tools import StructuredTool
from langchain_core.tools.base import BaseTool
from langgraph.graph import StateGraph, END, START
from langchain_core.runnables import Runnable
from auth0_ai.authorizers.types import AuthorizerParams
from ..types import Auth0Nodes
from .initialize_ciba import initialize_ciba
from .initialize_hitl import initialize_hitl
from .types import CIBAGraphOptions, CIBAOptions, ProtectedTool, BaseState

class CIBAGraph():
    def __init__(
        self,
        options: Optional[CIBAGraphOptions] = None,
        authorizer_params: Optional[AuthorizerParams] = None,
    ):
        self.options = options
        self.authorizer_params = authorizer_params
        self.tools: List[ProtectedTool] = []
        self.graph: Optional[StateGraph] = None

    def get_tools(self) -> List[ProtectedTool]:
        return self.tools

    def get_graph(self) -> Optional[StateGraph]:
        return self.graph

    def get_options(self) -> Optional[CIBAGraphOptions]:
        return self.options

    def get_authorizer_params(self) -> Optional[AuthorizerParams]:
        return self.authorizer_params

    def register_nodes(
        self,
        graph: StateGraph,
    ) -> StateGraph:
        self.graph = graph

        # Add CIBA HITL and CIBA nodes
        self.graph.add_node(Auth0Nodes.AUTH0_CIBA_HITL.value, initialize_hitl(self))
        self.graph.add_node(Auth0Nodes.AUTH0_CIBA.value, initialize_ciba(self))
        self.graph.add_conditional_edges(
            Auth0Nodes.AUTH0_CIBA.value,
            lambda state: END if getattr(state, "auth0", {}).get("error") else Auth0Nodes.AUTH0_CIBA_HITL.value,
        )

        return graph

    def protect_tool(
        self,
        tool: Union[BaseTool, Callable],
        options: CIBAOptions,
    ) -> StructuredTool:
        """
        Authorize Options to start CIBA flow.

        Attributes:
            tool (Union[BaseTool, Callable]): The tool to be protected.
            options (CIBAOptions): The CIBA options.
        """

        # Merge default options with tool-specific options
        merged_options = {**self.options, **options.__dict__} if isinstance(self.options, dict) else {**vars(self.options), **vars(options)}

        if merged_options["on_approve_go_to"] is None:
            raise ValueError(f"[{tool.name}] on_approve_go_to is required")

        if merged_options["on_reject_go_to"] is None:
            raise ValueError(f"[{tool.name}] on_reject_go_to is required")

        self.tools.append(ProtectedTool(tool_name=tool.name, options=merged_options))

        return tool

    def with_auth(self, path: Union[
            Callable[..., Union[Hashable, list[Hashable]]],
            Callable[..., Awaitable[Union[Hashable, list[Hashable]]]],
            Runnable[Any, Union[Hashable, list[Hashable]]],
        ]):
        """
        A wrapper for the callable that determines the next node or nodes using a protected tool.

        Attributes:
            path (Union[Callable[..., Union[Hashable, list[Hashable]]], Callable[..., Awaitable[Union[Hashable, list[Hashable]]]], Runnable[Any, Union[Hashable, list[Hashable]]]])): The callable that determines the next node or nodes using a protected tool.
        """
        def wrapper(*args):
            if not callable(path):
                return START

            state: BaseState = args[0]
            messages = state.get("messages")
            last_message = messages[-1] if messages else None

            # Call default path if there are no tool calls
            if not last_message or not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
                return path(*args)
            
            tool_name = last_message.tool_calls[0]["name"]
            tool = next((t for t in self.tools if t.tool_name == tool_name), None)
            
            if tool:
                return Auth0Nodes.AUTH0_CIBA.value

            # Call default path if tool is not protected
            return path(*args)

        return wrapper
