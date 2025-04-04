from typing import Awaitable, Callable
from langchain_core.messages import ToolMessage, AIMessage, ToolCall
from langgraph.types import interrupt, Command
from .types import ICIBAGraph, BaseState
from .utils import get_tool_definition
from auth0_ai.authorizers.ciba_authorizer import CibaAuthorizerCheckResponse

def initialize_hitl(ciba_graph: ICIBAGraph) -> Callable[[BaseState], Awaitable[Command]]:
    async def handler(state: BaseState) -> Command:
        tools = ciba_graph.get_tools()
        tool_definition = get_tool_definition(state, tools)

        # if no tool calls, resume
        if not tool_definition:
            return Command(resume=True)

        # wait for user approval
        human_review = interrupt("A push notification has been sent to your device.")

        metadata, tool, message = tool_definition["metadata"], tool_definition["tool"], tool_definition["message"]

        if human_review["status"] == CibaAuthorizerCheckResponse.APPROVED.value:
            updated_message = AIMessage(
                id=message.id,
                content="The user has approved the transaction",
                tool_calls=[
                    ToolCall(
                        name=tool["name"],
                        args=tool["args"],
                        id=tool["id"],
                    )
                ],
            )

            return Command(
                goto=metadata.options["on_approve_go_to"],
                update={"messages": [updated_message]},
            )
        else:
            tool_message = ToolMessage(
                name=tool["name"],
                content="The user has rejected the transaction.",
                tool_call_id=tool["id"],
            )
            return Command(
                goto=metadata.options["on_reject_go_to"],
                update={"messages": [tool_message]},
            )
    
    return handler
