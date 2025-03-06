import os
from typing import Any, Optional
from langgraph.types import Command
from langgraph_sdk import get_client
from auth0_ai.authorizers.ciba_authorizer import CIBAAuthorizer
from ..types import Auth0Graphs, Auth0Nodes
from .types import ICIBAGraph, State
from .utils import get_tool_definition

def initialize_ciba(ciba_graph: ICIBAGraph):
    async def handler(state: State, config: Optional[dict] = None) -> Any:
        try:
            ciba_params = ciba_graph.get_options()
            tools = ciba_graph.get_tools()
            tool_definition = get_tool_definition(state, tools)

            if not tool_definition:
                return Command(resume=True)

            graph = ciba_graph.get_graph()
            metadata, tool = tool_definition["metadata"], tool_definition["tool"]
            ciba_options = metadata.options
            binding_message = ""

            langgraph = get_client(url=os.getenv("LANGGRAPH_API_URL", "http://localhost:54367"))

            # Check if CIBA Poller Graph exists
            search_result = await langgraph.assistants.search({"graph_id": Auth0Graphs.CIBA_POLLER})
            if not search_result:
                raise ValueError(
                    f"[{Auth0Nodes.AUTH0_CIBA}] \"{Auth0Graphs.CIBA_POLLER}\" does not exist. Make sure to register the graph in your \"langgraph.json\"."
                )

            if metadata.options.on_approve_go_to not in graph.nodes:
                raise ValueError(f"[{Auth0Nodes.AUTH0_CIBA}] \"{metadata.options.on_approve_go_to}\" is not a valid node.")

            if metadata.options.on_reject_go_to not in graph.nodes:
                raise ValueError(f"[{Auth0Nodes.AUTH0_CIBA}] \"{metadata.options.on_reject_go_to}\" is not a valid node.")

            if not ciba_params or not ciba_params.config.scheduler:
                raise ValueError(f"[{Auth0Nodes.AUTH0_CIBA}] \"scheduler\" must be a \"function\" or a \"string\".")

            if not ciba_params.config.on_resume_invoke:
                raise ValueError(f"[{Auth0Nodes.AUTH0_CIBA}] \"on_resume_invoke\" must be defined.")

            if callable(ciba_options.binding_message):
                binding_message = await ciba_options.binding_message(tool.args)
            elif isinstance(ciba_options.binding_message, str):
                binding_message = ciba_options.binding_message

            ciba_response = await CIBAAuthorizer.start(
                {
                    "user_id": config.get("configurable", {}).get("user_id"),
                    "scope": ciba_options.scope or "openid",
                    "audience": ciba_options.audience,
                    "binding_message": binding_message,
                },
                ciba_graph.get_authorizer_params(),
            )

            scheduler = ciba_params.config.scheduler
            on_resume_invoke = ciba_params.config.on_resume_invoke
            thread_id = config.get("metadata", {}).get("thread_id")
            scheduler_params = {
                "tool_id": tool.id,
                "user_id": config.get("configurable", {}).get("user_id"),
                "ciba_graph_id": Auth0Graphs.CIBA_POLLER,
                "thread_id": thread_id,
                "ciba_response": ciba_response,
                "on_resume_invoke": on_resume_invoke,
            }

            # Use Custom Scheduler
            if callable(scheduler):
                await scheduler(scheduler_params)

            # Use Langgraph SDK to schedule the task
            elif isinstance(scheduler, str):
                await langgraph.crons.create_for_thread(
                    thread_id,
                    scheduler_params["ciba_graph_id"],
                    {
                        "schedule": {"unit": "minutes", "interval": 1},  # Default to every minute
                        "input": scheduler_params,
                    },
                )

            print("CIBA Task Scheduled")
        except Exception as e:
            print(e)
            state.auth0 = {"error": str(e)}

        return state

    return handler