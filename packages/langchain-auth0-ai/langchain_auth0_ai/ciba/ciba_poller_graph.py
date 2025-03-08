import os
from langgraph.graph import StateGraph, END, START
from typing import Awaitable, Callable, Union, Optional, TypedDict
from langgraph_sdk import get_client
from auth0_ai.authorizers.ciba_authorizer import CIBAAuthorizer, CibaAuthorizerCheckResponse, AuthorizeResponse
from auth0_ai.types import Credentials, TokenResponse
from langchain_auth0_ai.ciba.types import Auth0Graphs

class CibaState(TypedDict):
    ciba_response: AuthorizeResponse
    on_resume_invoke: str
    thread_id: str
    user_id: str
    
    # Internal
    task_id: str
    tool_id: str
    status: CibaAuthorizerCheckResponse
    token_response: Optional[TokenResponse]

def ciba_poller_graph(on_stop_scheduler: Union[str, Callable[[CibaState], Awaitable[None]]]):
    async def check_status(state: CibaState):
        try:
            res = await CIBAAuthorizer.check(state["ciba_response"]["auth_req_id"])
            state["token_response"] = res["token"]
            state["status"] = res["status"]
        except Exception as e:
            print(f"Error in check_status: {e}")
        return state
    
    async def stop_scheduler(state: CibaState):
        try:
            if isinstance(on_stop_scheduler, str):
                langgraph = get_client(url=os.getenv("LANGGRAPH_API_URL", "http://localhost:54367"))
                await langgraph.crons.create_for_thread(state.thread_id, Auth0Graphs.CIBA_POLLER.value)
            elif callable(on_stop_scheduler):
                await on_stop_scheduler(state)
        except Exception as e:
            print(f"Error in stop_scheduler: {e}")
        return state
    
    async def resume_agent(state: CibaState):
        langgraph = get_client(url=os.getenv("LANGGRAPH_API_URL", "http://localhost:54367"))
        _credentials: Credentials = None
        
        try:
            if state["status"] == CibaAuthorizerCheckResponse.APPROVED:
                _credentials = {
                    "access_token": {
                        "type": state["token_response"].get("tokenType", "Bearer"),
                        "value": state["token_response"].get("accessToken"),
                    }
                }

            await langgraph.runs.wait(
                thread_id=state["thread_id"],
                assistant_id=state["on_resume_invoke"],
                config={
                    "configurable": {"_credentials": _credentials} # this is only for this run / threadid
                },
                command={"resume": True}
            )
        except Exception as e:
            print(f"Error in resume_agent: {e}")
        
        return state
    
    async def should_continue(state: CibaState):
        if state["status"] == CibaAuthorizerCheckResponse.PENDING:
            return END
        elif state["status"] == CibaAuthorizerCheckResponse.EXPIRED:
            return "stop_scheduler"
        elif state["status"] in [CibaAuthorizerCheckResponse.APPROVED, CibaAuthorizerCheckResponse.REJECTED]:
            return "resume_agent"
        return END
    
    state_graph = StateGraph(CibaState)
    state_graph.add_node("check_status", check_status)
    state_graph.add_node("stop_scheduler", stop_scheduler)
    state_graph.add_node("resume_agent", resume_agent)
    state_graph.add_edge(START, "check_status")
    state_graph.add_edge("resume_agent", "stop_scheduler")
    state_graph.add_conditional_edges("check_status", should_continue)
    
    return state_graph