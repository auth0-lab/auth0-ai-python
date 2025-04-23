from typing import Annotated, Sequence, TypedDict

from langchain.storage import InMemoryStore
from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from src.agents.tools.check_user_calendar import check_user_calendar_tool
from src.agents.tools.list_repositories import list_github_repositories_tool


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


llm = ChatOpenAI(
    model="gpt-4o"
).bind_tools([check_user_calendar_tool, list_github_repositories_tool])


async def call_llm(state: State):
    response = await llm.ainvoke(state["messages"])
    return {"messages": [response]}


def route_after_llm(state: State):
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END


state_graph = (
    StateGraph(State)
    .add_node("call_llm", call_llm)
    .add_node(
        "tools",
        ToolNode(
            [
                # A tool with federated connection api access
                check_user_calendar_tool,
                list_github_repositories_tool,
                # ... any other tool without federated connection api access
            ],
            # The error handler should be disabled to allow interruptions to be triggered from within tools.
            handle_tool_errors=False
        )
    )
    .add_edge(START, "call_llm")
    .add_edge("tools", "call_llm")
    .add_conditional_edges("call_llm", route_after_llm, [END, "tools"])
)

checkpointer = MemorySaver()
graph = state_graph.compile()
