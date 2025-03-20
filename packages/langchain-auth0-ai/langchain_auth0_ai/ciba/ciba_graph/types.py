from typing import Optional, List, Callable, Union, Awaitable, TypedDict
from abc import ABC, abstractmethod
from langgraph.graph import StateGraph
from langchain_core.messages import AIMessage, ToolMessage
from auth0_ai.authorizers.types import AuthorizerParams
from auth0_ai.authorizers.ciba_authorizer import AuthorizeResponse

class Auth0State(TypedDict):
    error: str

class BaseState(TypedDict):
    task_id: str
    messages: List[Union[AIMessage, ToolMessage]]
    auth0: Optional[Auth0State] = None

class SchedulerParams:
    def __init__(
        self,
        user_id: str,
        thread_id: str,
        ciba_graph_id: str,
        ciba_response: AuthorizeResponse,
        tool_id: Optional[str] = None,
        on_resume_invoke: str = "",
    ):
        self.user_id = user_id
        self.thread_id = thread_id
        self.tool_id = tool_id
        self.on_resume_invoke = on_resume_invoke
        self.ciba_graph_id = ciba_graph_id
        self.ciba_response = ciba_response

class CIBAOptions():
    """
    The CIBA options.

    Attributes:
        binding_message (Union[str, Callable[..., Awaitable[str]]]): A human-readable string to display to the user, or a function that resolves it.
        scope (Optional[str]): Space-separated list of OIDC and custom API scopes.
        on_approve_go_to (Optional[str]): A node name to redirect the flow after user approval.
        on_reject_go_to (Optional[str]): A node name to redirect the flow after user rejection.
        audience (Optional[str]): Unique identifier of the audience for an issued token.
        request_expiry (Optional[int]): To configure a custom expiry time in seconds for CIBA request, pass a number between 1 and 300.
    """
    def __init__(
        self,
        binding_message: Union[str, Callable[..., Awaitable[str]]],
        scope: Optional[str] = None,
        on_approve_go_to: Optional[str] = None,
        on_reject_go_to: Optional[str] = None,
        audience: Optional[str] = None,
        request_expiry: Optional[int] = None,
    ):
        self.binding_message = binding_message
        self.scope = scope
        self.on_approve_go_to = on_approve_go_to
        self.on_reject_go_to = on_reject_go_to
        self.audience = audience
        self.request_expiry = request_expiry

class ProtectedTool():
    def __init__(self, tool_name: str, options: CIBAOptions):
        self.tool_name = tool_name
        self.options = options

class CIBAGraphOptionsConfig:
    def __init__(self, on_resume_invoke: str, scheduler: Union[str, Callable[[SchedulerParams], Awaitable[None]]]):
        self.on_resume_invoke = on_resume_invoke
        self.scheduler = scheduler

class CIBAGraphOptions():
    """
    The base CIBA options.

    Attributes:
        config (CIBAGraphOptionsConfig): Configuration options.
        scope (Optional[str]): Space-separated list of OIDC and custom API scopes.
        on_approve_go_to (Optional[str]): A node name to redirect the flow after user approval.
        on_reject_go_to (Optional[str]): A node name to redirect the flow after user rejection.
        audience (Optional[str]): Unique identifier of the audience for an issued token.
        request_expiry (Optional[int]): To configure a custom expiry time in seconds for CIBA request, pass a number between 1 and 300.
    """
    def __init__(
        self,
        config: CIBAGraphOptionsConfig,
        scope: Optional[str] = None,
        on_approve_go_to: Optional[str] = None,
        on_reject_go_to: Optional[str] = None,
        audience: Optional[str] = None,
        request_expiry: Optional[int] = None,
        
    ):
        self.config = config
        self.scope = scope
        self.on_approve_go_to = on_approve_go_to
        self.on_reject_go_to = on_reject_go_to
        self.audience = audience
        self.request_expiry = request_expiry

class ICIBAGraph(ABC):
    @abstractmethod
    def get_tools(self) -> List[ProtectedTool]:
        pass

    @abstractmethod
    def get_graph(self) -> StateGraph:
        pass

    @abstractmethod
    def get_authorizer_params(self) -> Optional[AuthorizerParams]:
        pass

    @abstractmethod
    def get_options(self) -> Optional[CIBAGraphOptions]:
        pass