# from langgraph.graph import StateGraph, END, START
# from langgraph.prebuilt import ToolNode
# from langgraph.checkpoint import MemorySaver
# from langgraph.store import InMemoryStore
# from langchain_core.messages import AIMessage
# from langgraph.schema import Annotation, MessagesAnnotation
# from auth0_ai_langchain import Auth0AI, Auth0State
# from services.client import SchedulerClient
# from tools import trade as trade_tool
# import os

# class ConditionalTrade:
#     def __init__(self, ticker: str, qty: int, metric: str, threshold: float, operator: str):
#         self.ticker = ticker
#         self.qty = qty
#         self.metric = metric
#         self.threshold = threshold
#         self.operator = operator

# async def should_continue(state):
#     messages = state["messages"]
#     last_message = messages[-1] if messages else None

#     if not isinstance(last_message, AIMessage) or not getattr(last_message, "tool_calls", None):
#         return END
#     return "tools"

# # This function should contains the logic to check if the stock condition is met.
# async def check_condition(state, config):
#     store = config["store"]
#     data = await store.get([state["task_id"]], "status")

#     if data and data.get("value", {}).get("status") == "processing":
#         # skip since the job is already processing
#         return state

#     if not data:
#         await store.put([state["task_id"]], "status", {"status": "processing"})

#     # Calling the trade tool to initiate the trade
#     return {
#         "messages": [
#             AIMessage(
#                 content="",
#                 tool_calls=[
#                     {
#                         "name": "trade_tool",
#                         "args": {
#                             "ticker": state["data"]["ticker"],
#                             "qty": state["data"]["qty"],
#                         },
#                         "id": "tool_abcd123",
#                     }
#                 ],
#             )
#         ]
#     }

# async def stop_scheduler(state):
#     try:
#         await SchedulerClient().stop(state["task_id"])
#     except Exception as e:
#         print("Error stopping scheduler:", e)
#     return state

# def notify_user(state):
#     print("----")
#     print("Notifying the user about the trade.")
#     print("----")
#     return state

# auth0_ai = Auth0AI()

# # TODO: Configure CIBA flow
# ciba = auth0_ai.withCIBA(
#     audience=os.getenv("AUDIENCE"),
#     config={
#         "onResumeInvoke": "conditional-trade",
#         "scheduler": lambda input: SchedulerClient().schedule(input["cibaGraphId"], {"input": input}),
#     }
# )

# StateAnnotation = Annotation.Root(
#     **MessagesAnnotation.spec,
#     **Auth0State.spec,
#     data=Annotation[ConditionalTrade]
# )

# state_graph = ciba.register_nodes(
#     StateGraph(StateAnnotation)
#     .add_node("checkCondition", check_condition)
#     .add_node("notifyUser", notify_user)
#     .add_node("stopScheduler", stop_scheduler)
#     .add_node(
#         "tools",
#         ToolNode([
#             ciba.protect_tool(
#                 trade_tool,
#                 on_approve_go_to="tools",
#                 on_reject_go_to="stopScheduler",
#                 scope="stock:trade",
#                 binding_message=lambda _: f"Do you want to buy {_.qty} {_.ticker}?",
#             )
#         ])
#     )
#     .add_edge(START, "checkCondition")
#     .add_edge("tools", "stopScheduler")
#     .add_edge("stopScheduler", "notifyUser")
#     .add_conditional_edges("checkCondition", ciba.with_auth(should_continue))
# )

# graph = state_graph.compile(checkpointer=MemorySaver(), store=InMemoryStore())
