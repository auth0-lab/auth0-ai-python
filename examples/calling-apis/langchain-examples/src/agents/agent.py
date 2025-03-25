from langgraph.graph import StateGraph, END, START, add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, AIMessage
from langchain.storage import InMemoryStore
from typing import TypedDict, Annotated, Sequence
from tools.check_country_holiday import check_country_holiday_tool
from tools.check_user_calendar import check_user_calendar_tool
from langchain_openai import ChatOpenAI
from langchain_auth0_ai.auth0_ai import Auth0AI

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

auth0_ai = Auth0AI()
with_calender_free_busy_access = auth0_ai.with_federated_connection(
    connection="google-oauth2",
    scopes=["https://www.googleapis.com/auth/calendar.freebusy"]
)

llm = ChatOpenAI(model="gpt-4o").bind_tools([check_country_holiday_tool, check_user_calendar_tool])

async def call_llm(state: State):
    response = await llm.ainvoke(state["messages"])
    return {"messages": [response]}

def route_after_llm(state: State):
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END

workflow = (
    StateGraph(State)
    .add_node("call_llm", call_llm)
    .add_node("tools", ToolNode([
        # A tool with federated connection api access
        with_calender_free_busy_access(check_user_calendar_tool),
        # A tool without federated connection api access
        check_country_holiday_tool,
    ]))
    .add_edge(START, "call_llm")
    .add_edge("tools", "call_llm")
    .add_conditional_edges("call_llm", route_after_llm, [END, "tools"])
)

graph = workflow.compile(checkpointer=MemorySaver(), store=InMemoryStore())
