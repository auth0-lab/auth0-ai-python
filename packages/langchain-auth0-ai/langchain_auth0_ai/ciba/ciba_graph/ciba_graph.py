from typing import Generic, List, Optional, TypeVar, Callable, Any
from langchain_core.tools import StructuredTool
from langgraph.graph import StateGraph, END, START
from auth0_ai.types import AuthorizerParams
from ..types import Auth0Nodes
from .initialize_ciba import initialize_ciba
from .initialize_hitl import initialize_hitl
from .types import CIBAGraphOptions, CIBAOptions, ProtectedTool, State

N = TypeVar("N", bound=str)

class CIBAGraph(Generic[N]):
    def __init__(
        self,
        options: Optional[CIBAGraphOptions[N]] = None,
        authorizer_params: Optional[AuthorizerParams] = None,
    ):
        self.graph: Optional[StateGraph] = None
        self.options = options
        self.tools: List[ProtectedTool[N]] = []
        self.authorizer_params = authorizer_params

    def get_tools(self) -> List[ProtectedTool[N]]:
        return self.tools

    def get_graph(self) -> Optional[StateGraph]:
        return self.graph

    def get_options(self) -> Optional[CIBAGraphOptions[N]]:
        return self.options

    def get_authorizer_params(self) -> Optional[AuthorizerParams]:
        return self.authorizer_params

    def register_nodes(
        self,
        graph: StateGraph,
    ) -> StateGraph:
        self.graph = graph

        # Add CIBA HITL and CIBA nodes
        self.graph.add_node(Auth0Nodes.AUTH0_CIBA_HITL, initialize_hitl(self))
        self.graph.add_node(Auth0Nodes.AUTH0_CIBA, initialize_ciba(self))
        self.graph.add_conditional_edges(
            Auth0Nodes.AUTH0_CIBA,
            lambda state: END if state.auth0 and state.auth0.get("error") else Auth0Nodes.AUTH0_CIBA_HITL,
        )

        return graph

    def protect_tool(
        self,
        tool: StructuredTool,
        options: CIBAOptions[N],
    ) -> StructuredTool:
        # Merge default options with tool-specific options
        merged_options = {**self.options, **options.__dict__} if isinstance(self.options, dict) else {**vars(self.options), **vars(options)}

        if merged_options["on_approve_go_to"] is None:
            raise ValueError(f"[{tool.name}] on_approve_go_to is required")

        if merged_options["on_reject_go_to"] is None:
            raise ValueError(f"[{tool.name}] on_reject_go_to is required")

        self.tools.append(ProtectedTool(tool_name=tool.name, options=merged_options))

        return tool

    def with_auth(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any) -> Any:
            state: State = args[0]
            messages = state.messages
            last_message = messages[-1] if messages else None

            if not callable(fn):
                return START

            # Call default function if no tool calls
            if not last_message or not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
                return fn(*args)

            tool_name = last_message.tool_calls[0].name
            tool = next((t for t in self.tools if t.tool_name == tool_name), None)

            if tool:
                return Auth0Nodes.AUTH0_CIBA

            # Call default function if tool is not protected
            return fn(*args)

        return wrapper
