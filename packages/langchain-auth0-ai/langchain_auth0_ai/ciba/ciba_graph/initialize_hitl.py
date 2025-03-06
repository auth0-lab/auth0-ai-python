from typing import Any, Awaitable, Callable
from langchain_core.messages import ToolMessage
from langgraph.types import interrupt, Command
from ..types import HumanResponse
from .types import ICIBAGraph, State
from .utils import get_tool_definition

def initialize_hitl(ciba_graph: ICIBAGraph) -> Callable[[State], Awaitable[Any]]:
    async def handler(state: State) -> Any:
        tools = ciba_graph.get_tools()
        tool_definition = get_tool_definition(state, tools)

        if not tool_definition:
            return Command(resume=True)

        metadata, tool, message = tool_definition["metadata"], tool_definition["tool"], tool_definition["message"]
        human_review = interrupt("A push notification has been sent to your device.")

        if human_review == HumanResponse.APPROVED:
            updated_message = {
                "role": "ai",
                "content": "The user has approved the transaction",
                "tool_calls": [
                    {
                        "id": tool.id,
                        "name": tool.name,
                        "args": tool.args,
                    }
                ],
                "id": message.id,
            }

            return Command(
                goto=metadata.options.on_approve_go_to,
                update={"messages": [updated_message]},
            )
        else:
            tool_message = ToolMessage(
                name=tool.name,
                content="The user has rejected the transaction.",
                tool_call_id=tool.id,
            )
            return Command(
                goto=metadata.options.on_reject_go_to,
                update={"messages": [tool_message]},
            )
    
    return handler
