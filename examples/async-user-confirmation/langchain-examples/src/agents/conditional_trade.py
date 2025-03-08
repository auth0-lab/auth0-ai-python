import os
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain.storage import InMemoryStore
from langchain_core.messages import AIMessage, ToolCall
from langchain_core.runnables.config import RunnableConfig
from src.agents.clients.scheduler import SchedulerClient
from langchain_auth0_ai.auth0_ai import Auth0AI
from langchain_auth0_ai.ciba.ciba_graph.types import State, CIBAOptions
from tools.trade import trade_tool

class ConditionalTrade(TypedDict):
    ticker: str
    qty: int;
    metric: str
    threshold: float;
    operator: str

class StateAnnotation(State):
    data: ConditionalTrade

def should_continue(state: StateAnnotation):
    messages = state.get("messages")
    last_message = messages[-1] if messages else None

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    
    return END

async def check_condition(state: StateAnnotation, config: RunnableConfig, store):
    """
    Checks the condition of a given state and config, and performs actions based on the status.
    
    :param state: The current state object containing task information.
    :param config: The configuration object for LangGraphRunnable, containing the store.
    :return: Updated state or an object containing messages with tool calls.
    """
    # TODO: This function should contains the logic to check if the stock condition is met.
    stored_status = await store.aget(state["task_id"], "status")

    if stored_status and stored_status.value == "processing":
        # Skip since the job is already processing
        return state

    if not stored_status:
        await store.aput(state["task_id"], "status", "processing")
    
    # Calling the trade tool to initiate the trade
    return {
        "messages": [
            AIMessage(
                id="message_abcd123",
                content="Calling trade tool...",
                tool_calls=[
                    ToolCall(
                        name="trade_tool",
                        args={
                            "ticker": state["data"]["ticker"],
                            "qty": state["data"]["qty"],
                        },
                        id="tool_abcd123",
                    )
                ]
            )
        ]
    }

async def stop_scheduler(state: StateAnnotation):
    await SchedulerClient().stop(state['task_id'])

async def notify_user(state: StateAnnotation):
    """
    Notifies the user about the trade.
    
    :param state: The current state of the trade.
    :return: The updated state after notification.
    """
    print("----")
    print("Notifying the user about the trade.")
    print("----")
    
    return state

# Configure CIBA flow with Auth0 AI
auth0_ai = Auth0AI()
async def scheduler(input):
    await SchedulerClient().schedule({
        "graph_id": input["ciba_graph_id"],
        "config": {},
        "input": input
    })

ciba = auth0_ai.with_CIBA(
    {
        "audience": os.getenv("AUDIENCE"),
        "config": {
            "on_resume_invoke": "conditional-trade",
            "scheduler": scheduler,
        },
    }
)

"""
Initializes and registers a state graph for conditional trade operations using CIBA.

The state graph consists of the following nodes:
- `check_condition`: Evaluates whether the trade condition is met.
- `notify_user`: Notifies the user about the trade status.
- `stop_scheduler`: Stops the scheduler if the trade is accepted or rejected.
- `tools`: A tool node that handles the trade tool with CIBA protection.

The `tools` node uses the `trade_tool` with CIBA protection, which includes:
- `on_approve_go_to`: Transitions to the `tools` node if the trade is approved.
- `on_reject_go_to`: Transitions to the `stop_scheduler` node if the trade is rejected.
- `scope`: Specifies the required scope for the trade operation (`stock:trade`).
- `binding_message`: Generates a message asking the user if they want to buy a specified quantity of a stock ticker.
"""
async def binding_message(ctx):
    return f"Authorize the purchase of {ctx['qty']} {ctx['ticker']}"

state_graph = StateGraph(StateAnnotation)
state_graph.add_node("check_condition", check_condition)
state_graph.add_node("notify_user", notify_user)
state_graph.add_node("stop_scheduler", stop_scheduler)
state_graph.add_node(
    "tools",
    ToolNode([
        ciba.protect_tool(
            trade_tool,
            options=CIBAOptions(
                on_approve_go_to="tools",
                on_reject_go_to="stop_scheduler",
                scope="stock:trade",
                binding_message=binding_message,
            )
        )
    ]),
)

state_graph.add_edge(START, "check_condition")
state_graph.add_edge("tools", "stop_scheduler")
state_graph.add_edge("stop_scheduler", "notify_user")
state_graph.add_conditional_edges("check_condition", ciba.with_auth(should_continue))

graph = ciba.register_nodes(state_graph).compile(checkpointer=MemorySaver(), store=InMemoryStore())