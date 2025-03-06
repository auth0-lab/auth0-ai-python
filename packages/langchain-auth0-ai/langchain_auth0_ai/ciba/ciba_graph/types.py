from typing import Optional, List, TypeVar, Generic, Callable, Union, Awaitable
from abc import ABC, abstractmethod
from langgraph.graph import StateGraph
from langchain_core.messages import AIMessage, ToolMessage
from auth0_ai.types import AuthorizerParams
from auth0_ai.authorizers.ciba_authorizer import AuthorizeResponse
from ...states import Auth0StateType

class State:
    def __init__(self, messages: List[Union[AIMessage, ToolMessage]], auth0: Optional[Auth0StateType] = None):
        self.messages = messages
        self.auth0 = auth0 if auth0 is not None else {}

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

N = TypeVar("N", bound=str)

class CIBAOptions(Generic[N]):
    def __init__(
        self,
        binding_message: Union[str, Callable[..., Awaitable[str]]],
        scope: Optional[str] = None,
        on_approve_go_to: Optional[N] = None,
        on_reject_go_to: Optional[N] = None,
        audience: Optional[str] = None,
        request_expiry: Optional[str] = None,
        subject_issuer_context: Optional[str] = None,
    ):
        self.binding_message = binding_message
        self.scope = scope
        self.on_approve_go_to = on_approve_go_to
        self.on_reject_go_to = on_reject_go_to
        self.audience = audience
        self.request_expiry = request_expiry
        self.subject_issuer_context = subject_issuer_context

class ProtectedTool(Generic[N]):
    def __init__(self, tool_name: str, options: CIBAOptions[N]):
        self.tool_name = tool_name
        self.options = options

class CIBAGraphOptionsConfig:
    def __init__(self, on_resume_invoke: str, scheduler: Union[str, Callable[[SchedulerParams], Awaitable[None]]]):
        self.on_resume_invoke = on_resume_invoke
        self.scheduler = scheduler

class CIBAGraphOptions(Generic[N]):
    def __init__(
        self,
        config: CIBAGraphOptionsConfig,
        scope: Optional[str] = None,
        on_approve_go_to: Optional[N] = None,
        on_reject_go_to: Optional[N] = None,
        audience: Optional[str] = None,
        request_expiry: Optional[str] = None,
        subject_issuer_context: Optional[str] = None,
        
    ):
        self.config = config
        self.scope = scope
        self.on_approve_go_to = on_approve_go_to
        self.on_reject_go_to = on_reject_go_to
        self.audience = audience
        self.request_expiry = request_expiry
        self.subject_issuer_context = subject_issuer_context

class ICIBAGraph(ABC, Generic[N]):
    @abstractmethod
    def get_tools(self) -> List[ProtectedTool[N]]:
        pass

    @abstractmethod
    def get_graph(self) -> StateGraph:
        pass

    @abstractmethod
    def get_authorizer_params(self) -> Optional[AuthorizerParams]:
        pass

    @abstractmethod
    def get_options(self) -> Optional[CIBAGraphOptions[N]]:
        pass