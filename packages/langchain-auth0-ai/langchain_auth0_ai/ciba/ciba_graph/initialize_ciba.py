import os
from langgraph.types import Command
from langgraph_sdk import get_client
from langchain_core.runnables.config import RunnableConfig
from auth0_ai.authorizers.ciba_authorizer import CIBAAuthorizer
from ..types import Auth0Graphs, Auth0Nodes
from .types import ICIBAGraph, BaseState
from .utils import get_tool_definition

def initialize_ciba(ciba_graph: ICIBAGraph):
    async def handler(state: BaseState, config: RunnableConfig):
        try:
            ciba_params = ciba_graph.get_options()
            tools = ciba_graph.get_tools()
            tool_definition = get_tool_definition(state, tools)

            if not tool_definition:
                return Command(resume=True)

            graph = ciba_graph.get_graph()
            metadata, tool = tool_definition["metadata"], tool_definition["tool"]
            ciba_options = metadata.options

            langgraph = get_client(url=os.getenv("LANGGRAPH_API_URL", "http://localhost:54367"))

            # Check if CIBA Poller Graph exists
            search_result = await langgraph.assistants.search(graph_id=Auth0Graphs.CIBA_POLLER.value)
            if not search_result:
                raise ValueError(
                    f"[{Auth0Nodes.AUTH0_CIBA}] \"{Auth0Graphs.CIBA_POLLER}\" does not exist. Make sure to register the graph in your \"langgraph.json\"."
                )

            if ciba_options["on_approve_go_to"] not in graph.nodes:
                raise ValueError(f"[{Auth0Nodes.AUTH0_CIBA}] \"{ciba_options["on_approve_go_to"]}\" is not a valid node.")

            if ciba_options["on_reject_go_to"] not in graph.nodes:
                raise ValueError(f"[{Auth0Nodes.AUTH0_CIBA}] \"{ciba_options["on_reject_go_to"]}\" is not a valid node.")

            scheduler = ciba_params.config["scheduler"]
            on_resume_invoke = ciba_params.config["on_resume_invoke"]
            audience = ciba_params.audience

            if not scheduler:
                raise ValueError(f"[{Auth0Nodes.AUTH0_CIBA}] \"scheduler\" must be a \"function\" or a \"string\".")

            if not on_resume_invoke:
                raise ValueError(f"[{Auth0Nodes.AUTH0_CIBA}] \"on_resume_invoke\" must be defined.")

            user_id = config.get("configurable", {}).get("user_id")
            thread_id = config.get("metadata", {}).get("thread_id")

            ciba_response = await CIBAAuthorizer.start(
                {
                    "user_id": user_id,
                    "scope": ciba_options["scope"] or "openid",
                    "audience": audience,
                    "binding_message": ciba_options["binding_message"],
                },
                ciba_graph.get_authorizer_params(),
                tool["args"],
            )

            scheduler_params = {
                "tool_id": tool["id"],
                "user_id": user_id,
                "ciba_graph_id": Auth0Graphs.CIBA_POLLER.value,
                "thread_id": thread_id,
                "ciba_response": ciba_response,
                "on_resume_invoke": on_resume_invoke,
            }

            if callable(scheduler):
                # Use Custom Scheduler
                await scheduler(scheduler_params)
            elif isinstance(scheduler, str):
                # Use Langgraph SDK to schedule the task
                await langgraph.crons.create_for_thread(
                    thread_id,
                    scheduler_params["ciba_graph_id"],
                    schedule="*/1 * * * *", # Default to every minute
                    input=scheduler_params,
                )

            print("CIBA Task Scheduled")
        except Exception as e:
            print(e)
            state["auth0"] = {"error": str(e)}

        return state

    return handler