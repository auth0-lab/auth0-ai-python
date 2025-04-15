from langgraph.graph import StateGraph, END, START, add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, AIMessage
from typing import TypedDict, Annotated, Sequence
from tools.trade import trade_tool
from tools.conditional_trade import conditional_trade_tool
from langchain_openai import ChatOpenAI

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

llm = ChatOpenAI(model="gpt-4o").bind_tools([trade_tool, conditional_trade_tool])

async def call_llm(state: State):
    response = await llm.ainvoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: State):
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END

state_graph = (
    StateGraph(State)
    .add_node("call_llm", call_llm)
    .add_node("tools", ToolNode([trade_tool, conditional_trade_tool]))
    .add_edge(START, "call_llm")
    .add_edge("tools", "call_llm")
    .add_conditional_edges("call_llm", should_continue)
)

graph = state_graph.compile(checkpointer=MemorySaver())
