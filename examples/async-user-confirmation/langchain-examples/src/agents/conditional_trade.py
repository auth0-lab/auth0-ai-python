import json
import os
from typing import Annotated, TypedDict
from auth0_ai_langchain.auth0_ai import Auth0AI
from langchain.storage import InMemoryStore
from langchain_core.messages import AIMessage, ToolCall, ToolMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables import ensure_config
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from src.agents.clients.scheduler import SchedulerClient
from tools.trade import trade_tool

class ConditionalTrade(TypedDict):
    ticker: str
    qty: int
    metric: str
    threshold: float
    operator: str

class State(TypedDict):
    task_id: str
    messages: Annotated[list, add_messages]
    data: ConditionalTrade

def should_continue(state: State):
    messages = state.get("messages")
    last_message = messages[-1] if messages else None

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"

    return END

async def check_condition(state: State, config: RunnableConfig):
    """
    Checks the condition of a given state and config, and performs actions based on the status.
    """
    # TODO: This function should contains the logic to check if the stock condition is met.
    condition_met = True

    if condition_met:
        print("Condition is met! Stopping the scheduler")
        await SchedulerClient().stop(state["task_id"])
    else:
        print("Condition is not met! Continuing with the scheduler")
        return

    print("Calling the trade tool to initiate the trade")
    return {
        "messages": [
            AIMessage(
                id="message_abcd123",
                content="",
                tool_calls=[
                    ToolCall(
                        id="tool_abcd123",
                        name="trade_tool",
                        args={
                            "ticker": state["data"]["ticker"],
                            "qty": state["data"]["qty"],
                        },
                    )
                ]
            )
        ]
    }

async def notify_user(state: State):
    """
    Notifies the user about the trade.

    :param state: The current state of the trade.
    :return: The updated state after notification.
    """
    details = "unknown"
    messages = state.get("messages")
    last_message = messages[-1] if messages else None
    if isinstance(last_message, ToolMessage):
        details = last_message.content

    print("----")
    print("Notifying the user about the trade.")
    print(f"Details: {details}")
    print("----")
    return state

def check_trade_status(state: State):
    messages = state.get("messages")
    last_message = messages[-1] if messages else None

    if (
        isinstance(last_message, ToolMessage)
        and last_message.name == "trade_tool"
        and isinstance(last_message.content, str)
    ):
        success = json.loads(last_message.content).get("success")
        return "notify_user" if success else END

    return END

auth0_ai = Auth0AI()
protect_tool = auth0_ai.with_async_user_confirmation(
    audience=os.getenv("AUDIENCE"),
    scope="stock:trade",
    binding_message=lambda ticker, qty: f"Authorize the purchase of {qty} {ticker}",
    user_id=lambda *_, **__: ensure_config().get("configurable", {}).get("user_id")
)

state_graph = StateGraph(State)
state_graph.add_node("check_condition", check_condition)
state_graph.add_node("notify_user", notify_user)
state_graph.add_node("tools", ToolNode([protect_tool(trade_tool)], handle_tool_errors=False))
state_graph.add_edge(START, "check_condition")
state_graph.add_conditional_edges("tools", check_trade_status, [END, "notify_user"])
state_graph.add_conditional_edges("check_condition", should_continue, [END, "tools"])

graph = state_graph.compile(checkpointer=MemorySaver(), store=InMemoryStore())
