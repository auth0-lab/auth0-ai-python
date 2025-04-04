import os
from langgraph.graph import StateGraph, END, START
from typing import Awaitable, Callable, Union, Optional, TypedDict
from langgraph_sdk import get_client
from langgraph_sdk.schema import Command
from auth0_ai.authorizers.ciba_authorizer import CIBAAuthorizer, CibaAuthorizerCheckResponse, AuthorizeResponse
from auth0_ai.credentials import Credentials
from auth0_ai.token_response import TokenResponse
from langchain_auth0_ai.ciba.types import Auth0Graphs

class State(TypedDict):
    ciba_response: AuthorizeResponse
    on_resume_invoke: str
    thread_id: str
    user_id: str
    
    # Internal
    task_id: str
    tool_id: str
    status: CibaAuthorizerCheckResponse
    token_response: Optional[TokenResponse]

def ciba_poller_graph(on_stop_scheduler: Union[str, Callable[[State], Awaitable[None]]]):
    """
    A LangGraph graph to monitor the status of a CIBA transaction.

    Attributes:
        on_stop_scheduler (Union[str, Callable[[State], Awaitable[None]]]): A graph name to redirect the flow, or a function to execute when the CIBA transaction expires.
    """
    async def check_status(state: State):
        try:
            res = await CIBAAuthorizer.check(state["ciba_response"]["auth_req_id"])
            state["token_response"] = res.get("token")
            state["status"] = res.get("status")
        except Exception as e:
            print(f"Error in check_status: {e}")
        return state
    
    async def stop_scheduler(state: State):
        try:
            if isinstance(on_stop_scheduler, str):
                langgraph = get_client(url=os.getenv("LANGGRAPH_API_URL", "http://localhost:54367"))
                await langgraph.crons.create_for_thread(state.thread_id, Auth0Graphs.CIBA_POLLER.value)
            elif callable(on_stop_scheduler):
                await on_stop_scheduler(state)
        except Exception as e:
            print(f"Error in stop_scheduler: {e}")
        return state
    
    async def resume_agent(state: State):
        langgraph = get_client(url=os.getenv("LANGGRAPH_API_URL", "http://localhost:54367"))
        _credentials: Credentials = None
        
        try:
            if state["status"] == CibaAuthorizerCheckResponse.APPROVED:
                _credentials = {
                    "access_token": {
                        "type": state["token_response"].get("token_type", "Bearer"),
                        "value": state["token_response"].get("access_token"),
                    }
                }

            await langgraph.runs.wait(
                state["thread_id"],
                state["on_resume_invoke"],
                config={
                    "configurable": {"_credentials": _credentials} # this is only for this run / thread_id
                },
                command=Command(resume={"status": state["status"]})
            )
        except Exception as e:
            print(f"Error in resume_agent: {e}")
        
        return state
    
    async def should_continue(state: State):
        status = state.get("status")
        if status == CibaAuthorizerCheckResponse.PENDING:
            return END
        elif status == CibaAuthorizerCheckResponse.EXPIRED:
            return "stop_scheduler"
        elif status in [CibaAuthorizerCheckResponse.APPROVED, CibaAuthorizerCheckResponse.REJECTED]:
            return "resume_agent"
        return END
    
    state_graph = StateGraph(State)
    state_graph.add_node("check_status", check_status)
    state_graph.add_node("stop_scheduler", stop_scheduler)
    state_graph.add_node("resume_agent", resume_agent)
    state_graph.add_edge(START, "check_status")
    state_graph.add_edge("resume_agent", "stop_scheduler")
    state_graph.add_conditional_edges("check_status", should_continue)
    
    return state_graph